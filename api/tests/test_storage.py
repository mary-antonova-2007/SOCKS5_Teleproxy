from __future__ import annotations

from pathlib import Path

from telegram_socks5_api.models import AdminRecord, ProxyUserRecord, UsersState
from telegram_socks5_api.storage import JsonStorage


def test_storage_roundtrip(tmp_path):
    storage = JsonStorage(tmp_path / "users.json")
    state = UsersState(
        admins=[AdminRecord(username="admin", password_hash="pbkdf2_sha256$1$salt$hash")],
        proxy_users=[ProxyUserRecord(username="proxy", password_hash="nt$ABC", enabled=True)],
    )
    storage.save_state(state)

    loaded = storage.load_state()
    assert loaded.admins[0].username == "admin"
    assert loaded.proxy_users[0].username == "proxy"


def test_storage_update(tmp_path):
    storage = JsonStorage(tmp_path / "users.json")

    result = storage.update(lambda state: state.admins.append(AdminRecord(username="admin", password_hash="hash")) or "ok")
    assert result == "ok"
    assert storage.load_state().admins[0].username == "admin"
