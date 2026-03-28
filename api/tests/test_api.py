from __future__ import annotations

from fastapi.testclient import TestClient

import telegram_socks5_api.main as main_module
from telegram_socks5_api.main import create_app
from telegram_socks5_api.proxy import ProxyConfigRenderer
from telegram_socks5_api.service import TelegramSocks5Service
from telegram_socks5_api.settings import get_settings
from telegram_socks5_api.storage import JsonStorage

from conftest import DummyReloader


def build_client() -> TestClient:
    settings = get_settings()
    service = TelegramSocks5Service(
        settings=settings,
        storage=JsonStorage(settings.users_file),
        renderer=ProxyConfigRenderer(settings),
        reloader=DummyReloader(),
    )
    if hasattr(main_module.get_settings, "cache_clear"):
        main_module.get_settings.cache_clear()
    if hasattr(main_module.get_service, "cache_clear"):
        main_module.get_service.cache_clear()
    main_module.get_settings = lambda: settings
    main_module.get_service = lambda: service
    return TestClient(create_app())


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_proxy_user_crud(env_isolated):
    with build_client() as client:
        admin_headers = auth_headers(client, "admin", "admin-secret")

        created = client.post(
            "/proxy-users",
            headers=admin_headers,
            json={"username": "telegram01", "password": "proxy-secret", "enabled": True},
        )
        assert created.status_code == 201, created.text
        assert created.json()["username"] == "telegram01"

        listed = client.get("/proxy-users", headers=admin_headers)
        assert listed.status_code == 200
        assert [row["username"] for row in listed.json()] == ["telegram01"]

        updated = client.patch(
            "/proxy-users/telegram01",
            headers=admin_headers,
            json={"password": "proxy-secret-2", "enabled": False},
        )
        assert updated.status_code == 200
        assert updated.json()["enabled"] is False

        deleted = client.delete("/proxy-users/telegram01", headers=admin_headers)
        assert deleted.status_code == 200

        listed = client.get("/proxy-users", headers=admin_headers)
        assert listed.status_code == 200
        assert listed.json() == []


def test_admin_panel_index(env_isolated):
    with build_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SOCKS5 TeleProxy Admin" in response.text


def test_superadmin_only_admin_endpoints(env_isolated):
    with build_client() as client:
        admin_headers = auth_headers(client, "admin", "admin-secret")
        super_headers = auth_headers(client, "superadmin", "super-secret")

        forbidden = client.get("/admins", headers=admin_headers)
        assert forbidden.status_code == 403

        created = client.post(
            "/admins",
            headers=super_headers,
            json={"username": "secondadmin", "password": "admin-secret-2"},
        )
        assert created.status_code == 201, created.text

        listed = client.get("/admins", headers=super_headers)
        assert listed.status_code == 200
        assert [row["username"] for row in listed.json()] == ["admin", "secondadmin"]
