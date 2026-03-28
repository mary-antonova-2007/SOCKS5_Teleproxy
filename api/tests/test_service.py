from __future__ import annotations

import pytest

from telegram_socks5_api.errors import ConflictError, PermissionDeniedError
from telegram_socks5_api.proxy import ProxyConfigRenderer
from telegram_socks5_api.security import verify_admin_password
from telegram_socks5_api.service import TelegramSocks5Service
from telegram_socks5_api.settings import get_settings
from telegram_socks5_api.storage import JsonStorage
from conftest import DummyReloader


def make_service():
    settings = get_settings()
    return TelegramSocks5Service(
        settings=settings,
        storage=JsonStorage(settings.users_file),
        renderer=ProxyConfigRenderer(settings),
        reloader=DummyReloader(),
    )


def test_bootstrap_and_login(env_isolated):
    service = make_service()
    row = service.bootstrap_admin("admin", "admin-secret")
    assert row.username == "admin"
    username, role = service.login("admin", "admin-secret")
    assert username == "admin"
    assert role == "admin"
    username, role = service.login("superadmin", "super-secret")
    assert username == "superadmin"
    assert role == "superadmin"


def test_proxy_user_crud(env_isolated):
    service = make_service()
    service.bootstrap_admin("admin", "admin-secret")
    created = service.create_proxy_user("tg-user", "proxy-secret", enabled=True, current_role="admin")
    assert created.username == "tg-user"
    config = service.render_config()
    assert "users tg-user:NT:" in config
    updated = service.update_proxy_user("tg-user", password="proxy-secret-2", enabled=False, current_role="admin")
    assert updated.enabled is False
    assert "users tg-user:NT:" not in service.render_config()
    service.delete_proxy_user("tg-user", current_role="admin")
    assert service.list_proxy_users() == []


def test_admin_management_requires_superadmin(env_isolated):
    service = make_service()
    service.bootstrap_admin("admin", "admin-secret")
    with pytest.raises(PermissionDeniedError):
        service.create_admin("second", "secret", current_role="admin")
    created = service.create_admin("second", "secret", current_role="superadmin")
    assert created.username == "second"
    updated = service.update_admin_password("second", "new-secret", current_role="superadmin")
    assert verify_admin_password("new-secret", updated.password_hash)
    service.delete_admin("second", current_role="superadmin")
    assert [row.username for row in service.list_admins()] == ["admin"]


def test_delete_last_admin_denied(env_isolated):
    service = make_service()
    service.bootstrap_admin("admin", "admin-secret")
    with pytest.raises(ConflictError):
        service.delete_admin("admin", current_role="superadmin")
