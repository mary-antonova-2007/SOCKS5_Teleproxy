from __future__ import annotations

import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from .md4 import nt_hash
from .errors import AuthenticationError, ValidationError
from .settings import Settings


PBKDF2_ITERATIONS = 210_000


def _salt() -> str:
    return secrets.token_urlsafe(16)


def hash_admin_password(password: str, *, salt: str | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    if not password:
        raise ValidationError("Password must not be empty")
    salt = salt or _salt()
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    digest = base64.urlsafe_b64encode(derived).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_admin_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations_raw, salt, digest = encoded.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    try:
        iterations = int(iterations_raw)
    except ValueError:
        return False
    candidate = hash_admin_password(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(candidate, encoded)


def hash_proxy_password(password: str) -> str:
    if not password:
        raise ValidationError("Password must not be empty")
    return f"nt${nt_hash(password)}"


def verify_proxy_password(password: str, encoded: str) -> bool:
    try:
        scheme, digest = encoded.split("$", 1)
    except ValueError:
        return False
    if scheme != "nt":
        return False
    return hmac.compare_digest(f"nt${nt_hash(password)}", encoded)


def create_access_token(*, settings: Settings, subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
        "iss": settings.service_name,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, *, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.service_name,
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc
    if not isinstance(payload, dict):
        raise AuthenticationError("Invalid token payload")
    return payload
