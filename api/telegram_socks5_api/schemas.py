from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


USERNAME_PATTERN = r"^[A-Za-z0-9._-]{3,64}$"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    username: str
    role: str


class ProxyUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=1, max_length=256)
    enabled: bool = True


class ProxyUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=256)
    enabled: bool | None = None


class ProxyUserOut(BaseModel):
    username: str
    enabled: bool
    created_at: str
    updated_at: str


class AdminCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=1, max_length=256)


class AdminPasswordUpdate(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class AdminOut(BaseModel):
    username: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    proxy_users: int
    admins: int


class CurrentUser(BaseModel):
    username: str
    role: str

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"
