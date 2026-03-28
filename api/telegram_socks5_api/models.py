from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class AdminRecord:
    username: str
    password_hash: str
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class ProxyUserRecord:
    username: str
    password_hash: str
    enabled: bool = True
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class UsersState:
    version: int = 1
    admins: list[AdminRecord] = field(default_factory=list)
    proxy_users: list[ProxyUserRecord] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def clone(self) -> "UsersState":
        return UsersState(
            version=self.version,
            admins=[replace(item) for item in self.admins],
            proxy_users=[replace(item) for item in self.proxy_users],
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "admins": [asdict(item) for item in self.admins],
            "proxy_users": [asdict(item) for item in self.proxy_users],
            "meta": {
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "UsersState":
        payload = payload or {}
        meta = payload.get("meta") or {}
        admins = [
            AdminRecord(
                username=str(row.get("username", "")).strip(),
                password_hash=str(row.get("password_hash", "")).strip(),
                created_at=str(row.get("created_at") or meta.get("created_at") or utc_now()),
                updated_at=str(row.get("updated_at") or meta.get("updated_at") or utc_now()),
            )
            for row in payload.get("admins", [])
            if str(row.get("username", "")).strip()
        ]
        proxy_users = [
            ProxyUserRecord(
                username=str(row.get("username", "")).strip(),
                password_hash=str(row.get("password_hash", "")).strip(),
                enabled=bool(row.get("enabled", True)),
                created_at=str(row.get("created_at") or meta.get("created_at") or utc_now()),
                updated_at=str(row.get("updated_at") or meta.get("updated_at") or utc_now()),
            )
            for row in payload.get("proxy_users", [])
            if str(row.get("username", "")).strip()
        ]
        return cls(
            version=int(payload.get("version", 1)),
            admins=admins,
            proxy_users=proxy_users,
            created_at=str(meta.get("created_at") or payload.get("created_at") or utc_now()),
            updated_at=str(meta.get("updated_at") or payload.get("updated_at") or utc_now()),
        )
