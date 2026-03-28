from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def _env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    users_file: Path
    proxy_config_file: Path
    proxy_pid_file: Path
    proxy_log_file: Path
    proxy_reload_request_file: Path
    proxy_reload_status_file: Path
    api_host: str
    api_port: int
    socks5_port: int
    jwt_secret: str
    jwt_algorithm: str
    jwt_expires_minutes: int
    superadmin_username: str
    superadmin_password: str
    initial_admin_username: str
    initial_admin_password: str
    service_name: str = "telegram-socks5-api"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_reload_request_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_reload_status_file.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    data_dir = Path(_env_str("SOCKS5_DATA_DIR", "/data")).expanduser().resolve()
    users_file = Path(_env_str("SOCKS5_USERS_FILE", str(data_dir / "users.json"))).expanduser().resolve()
    proxy_config_file = Path(
        _env_str("SOCKS5_PROXY_CONFIG_FILE", str(data_dir / "3proxy.cfg"))
    ).expanduser().resolve()
    proxy_pid_file = Path(
        _env_str("SOCKS5_PROXY_PID_FILE", str(data_dir / "3proxy.pid"))
    ).expanduser().resolve()
    proxy_log_file = Path(
        _env_str("SOCKS5_PROXY_LOG_FILE", str(data_dir / "3proxy.log"))
    ).expanduser().resolve()
    proxy_reload_request_file = Path(
        _env_str("SOCKS5_PROXY_RELOAD_REQUEST_FILE", str(data_dir / "3proxy.reload"))
    ).expanduser().resolve()
    proxy_reload_status_file = Path(
        _env_str("SOCKS5_PROXY_RELOAD_STATUS_FILE", str(data_dir / "3proxy.reload.status"))
    ).expanduser().resolve()
    return Settings(
        data_dir=data_dir,
        users_file=users_file,
        proxy_config_file=proxy_config_file,
        proxy_pid_file=proxy_pid_file,
        proxy_log_file=proxy_log_file,
        proxy_reload_request_file=proxy_reload_request_file,
        proxy_reload_status_file=proxy_reload_status_file,
        api_host=_env_str("API_HOST", "0.0.0.0"),
        api_port=_env_int("API_PORT", 8000),
        socks5_port=_env_int("SOCKS5_PORT", 1080),
        jwt_secret=_env_str("JWT_SECRET", "change-me"),
        jwt_algorithm=_env_str("JWT_ALGORITHM", "HS256"),
        jwt_expires_minutes=_env_int("JWT_EXPIRES_MINUTES", 60 * 24),
        superadmin_username=_env_str("SUPERADMIN_USERNAME", "superadmin"),
        superadmin_password=_env_str("SUPERADMIN_PASSWORD", "change-me"),
        initial_admin_username=_env_str("INITIAL_ADMIN_USERNAME", "admin"),
        initial_admin_password=_env_str("INITIAL_ADMIN_PASSWORD", ""),
    )
