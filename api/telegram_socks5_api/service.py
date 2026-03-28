from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable

from .errors import AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError, ValidationError, ReloadError
from .models import AdminRecord, ProxyUserRecord, UsersState, utc_now
from .proxy import ProxyConfigRenderer, ProxyReloader
from .security import create_access_token, hash_admin_password, hash_proxy_password, verify_admin_password
from .settings import Settings
from .storage import JsonStorage


def _clean_username(value: str) -> str:
    username = str(value or "").strip()
    if not username:
        raise ValidationError("Username is required")
    if len(username) < 3 or len(username) > 64:
        raise ValidationError("Username must be between 3 and 64 characters")
    allowed = all(ch.isalnum() or ch in "._-" for ch in username)
    if not allowed:
        raise ValidationError("Username may contain only letters, numbers, dot, underscore and dash")
    return username


class TelegramSocks5Service:
    def __init__(
        self,
        settings: Settings,
        storage: JsonStorage | None = None,
        renderer: ProxyConfigRenderer | None = None,
        reloader: ProxyReloader | None = None,
    ):
        self.settings = settings
        self.storage = storage or JsonStorage(settings.users_file)
        self.renderer = renderer or ProxyConfigRenderer(settings)
        self.reloader = reloader or ProxyReloader(settings)

    def ensure_runtime(self) -> UsersState:
        self.settings.ensure_dirs()
        state = self.storage.load_state()
        if (
            not state.admins
            and self.settings.initial_admin_password
            and self.settings.initial_admin_username != self.settings.superadmin_username
        ):
            bootstrap = AdminRecord(
                username=_clean_username(self.settings.initial_admin_username),
                password_hash=hash_admin_password(self.settings.initial_admin_password),
            )
            state.admins.append(bootstrap)
            state.touch()
            self.storage.save_state(state)
            state = self.storage.load_state()
        self.renderer.write(state)
        return state

    def _persist_state(self, state: UsersState, *, reload_proxy: bool = True) -> UsersState:
        original = self.storage.load_state()
        self.storage.save_state(state)
        self.renderer.write(state)
        if reload_proxy:
            try:
                self.reloader.reload()
            except ReloadError:
                self.storage.save_state(original)
                self.renderer.write(original)
                raise
        return state

    def bootstrap_admin(self, username: str, password: str, *, force: bool = False) -> AdminRecord:
        username = _clean_username(username)
        if username == self.settings.superadmin_username:
            raise ConflictError("Bootstrap admin must not reuse the superadmin username")
        state = self.storage.load_state()
        existing = self.get_admin_optional(state, username)
        if existing and not force:
            return existing
        record = AdminRecord(username=username, password_hash=hash_admin_password(password))
        if existing:
            state.admins = [item for item in state.admins if item.username != username]
        state.admins.append(record)
        state.touch()
        self._persist_state(state, reload_proxy=False)
        return record

    def login(self, username: str, password: str) -> tuple[str, str]:
        username = _clean_username(username)
        if username == self.settings.superadmin_username:
            if password != self.settings.superadmin_password:
                raise AuthenticationError("Invalid superadmin credentials")
            return username, "superadmin"
        state = self.storage.load_state()
        admin = self.get_admin_optional(state, username)
        if not admin or not verify_admin_password(password, admin.password_hash):
            raise AuthenticationError("Invalid credentials")
        return username, "admin"

    def get_admin_optional(self, state: UsersState, username: str) -> AdminRecord | None:
        username = _clean_username(username)
        for admin in state.admins:
            if admin.username == username:
                return admin
        return None

    def get_proxy_optional(self, state: UsersState, username: str) -> ProxyUserRecord | None:
        username = _clean_username(username)
        for user in state.proxy_users:
            if user.username == username:
                return user
        return None

    def list_admins(self) -> list[AdminRecord]:
        return sorted(self.storage.load_state().admins, key=lambda row: row.username.lower())

    def list_proxy_users(self) -> list[ProxyUserRecord]:
        return sorted(self.storage.load_state().proxy_users, key=lambda row: row.username.lower())

    def create_admin(self, username: str, password: str, *, current_role: str) -> AdminRecord:
        if current_role != "superadmin":
            raise PermissionDeniedError("Only superadmin can manage admins")
        username = _clean_username(username)
        if username == self.settings.superadmin_username:
            raise ConflictError("Built-in superadmin is managed from environment, not JSON")
        state = self.storage.load_state()
        if self.get_admin_optional(state, username):
            raise ConflictError("Admin already exists")
        record = AdminRecord(username=username, password_hash=hash_admin_password(password))
        state.admins.append(record)
        state.touch()
        self._persist_state(state)
        return record

    def update_admin_password(self, username: str, password: str, *, current_role: str) -> AdminRecord:
        if current_role != "superadmin":
            raise PermissionDeniedError("Only superadmin can manage admins")
        username = _clean_username(username)
        if username == self.settings.superadmin_username:
            raise ConflictError("Built-in superadmin password is managed from environment")
        state = self.storage.load_state()
        updated = False
        for index, admin in enumerate(state.admins):
            if admin.username == username:
                state.admins[index] = replace(admin, password_hash=hash_admin_password(password), updated_at=utc_now())
                updated = True
                record = state.admins[index]
                break
        if not updated:
            raise NotFoundError("Admin not found")
        state.touch()
        self._persist_state(state)
        return record

    def delete_admin(self, username: str, *, current_role: str) -> None:
        if current_role != "superadmin":
            raise PermissionDeniedError("Only superadmin can manage admins")
        username = _clean_username(username)
        if username == self.settings.superadmin_username:
            raise ConflictError("Built-in superadmin cannot be deleted")
        state = self.storage.load_state()
        admins = [admin for admin in state.admins if admin.username != username]
        if len(admins) == len(state.admins):
            raise NotFoundError("Admin not found")
        if len(admins) < 1:
            raise ConflictError("At least one admin must remain")
        state.admins = admins
        state.touch()
        self._persist_state(state)

    def create_proxy_user(self, username: str, password: str, *, enabled: bool, current_role: str) -> ProxyUserRecord:
        if current_role not in {"admin", "superadmin"}:
            raise PermissionDeniedError("Authentication required")
        username = _clean_username(username)
        state = self.storage.load_state()
        if self.get_proxy_optional(state, username):
            raise ConflictError("Proxy user already exists")
        record = ProxyUserRecord(username=username, password_hash=hash_proxy_password(password), enabled=enabled)
        state.proxy_users.append(record)
        state.touch()
        self._persist_state(state)
        return record

    def update_proxy_user(
        self,
        username: str,
        *,
        password: str | None,
        enabled: bool | None,
        current_role: str,
    ) -> ProxyUserRecord:
        if current_role not in {"admin", "superadmin"}:
            raise PermissionDeniedError("Authentication required")
        username = _clean_username(username)
        state = self.storage.load_state()
        for index, user in enumerate(state.proxy_users):
            if user.username == username:
                updated_user = user
                if password is not None:
                    updated_user = replace(updated_user, password_hash=hash_proxy_password(password))
                if enabled is not None:
                    updated_user = replace(updated_user, enabled=enabled)
                updated_user = replace(updated_user, updated_at=utc_now())
                state.proxy_users[index] = updated_user
                state.touch()
                self._persist_state(state)
                return updated_user
        raise NotFoundError("Proxy user not found")

    def delete_proxy_user(self, username: str, *, current_role: str) -> None:
        if current_role not in {"admin", "superadmin"}:
            raise PermissionDeniedError("Authentication required")
        username = _clean_username(username)
        state = self.storage.load_state()
        proxy_users = [user for user in state.proxy_users if user.username != username]
        if len(proxy_users) == len(state.proxy_users):
            raise NotFoundError("Proxy user not found")
        state.proxy_users = proxy_users
        state.touch()
        self._persist_state(state)

    def render_config(self) -> str:
        return self.renderer.render(self.storage.load_state())

    def save_config_only(self) -> Path:
        state = self.storage.load_state()
        return self.renderer.write(state)

    def authenticate_request_user(self, username: str, password: str) -> tuple[str, str]:
        return self.login(username, password)
