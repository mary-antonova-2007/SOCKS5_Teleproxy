from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@dataclass
class DummyReloader:
    calls: int = 0

    def reload(self) -> None:
        self.calls += 1


@pytest.fixture
def env_isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("SOCKS5_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SOCKS5_USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.setenv("SOCKS5_PROXY_CONFIG_FILE", str(tmp_path / "3proxy.cfg"))
    monkeypatch.setenv("SOCKS5_PROXY_PID_FILE", str(tmp_path / "3proxy.pid"))
    monkeypatch.setenv("SOCKS5_PROXY_LOG_FILE", str(tmp_path / "3proxy.log"))
    monkeypatch.setenv("SOCKS5_PROXY_RELOAD_REQUEST_FILE", str(tmp_path / "reload.request"))
    monkeypatch.setenv("SOCKS5_PROXY_RELOAD_STATUS_FILE", str(tmp_path / "reload.status"))
    monkeypatch.setenv("SOCKS5_PORT", "1080")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("SUPERADMIN_USERNAME", "superadmin")
    monkeypatch.setenv("SUPERADMIN_PASSWORD", "super-secret")
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("JWT_SECRET", "jwt-secret-for-tests-which-is-long-enough")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "60")
    from telegram_socks5_api.settings import get_settings
    from telegram_socks5_api.main import get_service

    get_settings.cache_clear()
    if hasattr(get_service, "cache_clear"):
        get_service.cache_clear()
    yield tmp_path
    get_settings.cache_clear()
    if hasattr(get_service, "cache_clear"):
        get_service.cache_clear()
