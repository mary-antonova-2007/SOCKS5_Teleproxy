from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import time
import uuid

from .errors import ReloadError
from .models import ProxyUserRecord, UsersState
from .settings import Settings


def _render_users_line(users: list[ProxyUserRecord]) -> str:
    active = [user for user in users if user.enabled]
    if not active:
        return ""
    parts = [f"{user.username}:NT:{user.password_hash.split('$', 1)[1]}" for user in active]
    return "users " + " ".join(parts)


class ProxyConfigRenderer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def render(self, state: UsersState) -> str:
        lines = [
            f"pidfile {self.settings.proxy_pid_file}",
            f"log {self.settings.proxy_log_file} D",
            "rotate 30",
            "nscache 65536",
            f"monitor {self.settings.proxy_config_file}",
            "timeouts 1 5 30 60 180 1800 15 60",
            "auth strong",
            "flush",
        ]
        users_line = _render_users_line(state.proxy_users)
        if users_line:
            lines.append(users_line)
        lines.extend(
            [
                "allow *",
                f"socks -p{self.settings.socks5_port} -i0.0.0.0",
            ]
        )
        return "\n".join(lines) + "\n"

    def write(self, state: UsersState) -> Path:
        self.settings.ensure_dirs()
        content = self.render(state)
        temp_path = self.settings.proxy_config_file.with_name(
            f".{self.settings.proxy_config_file.name}.tmp"
        )
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(self.settings.proxy_config_file)
        return self.settings.proxy_config_file


class ProxyReloader:
    def __init__(self, settings: Settings):
        self.settings = settings

    def reload(self) -> None:
        request_id = str(uuid.uuid4())
        request_file = self.settings.proxy_reload_request_file
        status_file = self.settings.proxy_reload_status_file
        temp_file = request_file.with_name(f".{request_file.name}.tmp")

        payload = {"request_id": request_id}
        temp_file.write_text(json.dumps(payload), encoding="utf-8")
        temp_file.replace(request_file)

        deadline = time.time() + 10
        while time.time() < deadline:
            if status_file.exists():
                try:
                    status = json.loads(status_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    time.sleep(0.2)
                    continue
                if status.get("request_id") != request_id:
                    time.sleep(0.2)
                    continue
                if status.get("status") == "ok":
                    return
                raise ReloadError(status.get("detail") or "Proxy reload failed")
            time.sleep(0.2)

        raise ReloadError("Timed out waiting for proxy reload")


def snapshot_proxy_state(state: UsersState) -> dict:
    return {
        "proxy_users": [asdict(item) for item in state.proxy_users if item.enabled],
        "active_count": sum(1 for item in state.proxy_users if item.enabled),
    }
