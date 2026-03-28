from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from .errors import AppError, AuthenticationError
from .schemas import (
    AdminCreate,
    AdminOut,
    AdminPasswordUpdate,
    CurrentUser,
    HealthResponse,
    LoginRequest,
    MessageResponse,
    ProxyUserCreate,
    ProxyUserOut,
    ProxyUserUpdate,
    TokenResponse,
)
from .security import create_access_token, decode_access_token
from .service import TelegramSocks5Service
from .settings import get_settings


bearer = HTTPBearer(auto_error=False)
PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"


def _find_media_dir() -> Path | None:
    candidates = [
        Path("/app/media"),
        PACKAGE_DIR.parent / "media",
        PACKAGE_DIR.parent.parent / "media",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@lru_cache(maxsize=1)
def get_service() -> TelegramSocks5Service:
    settings = get_settings()
    return TelegramSocks5Service(settings)


def _to_proxy_user_out(user) -> ProxyUserOut:
    return ProxyUserOut(
        username=user.username,
        enabled=user.enabled,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _to_admin_out(admin) -> AdminOut:
    return AdminOut(
        username=admin.username,
        created_at=admin.created_at,
        updated_at=admin.updated_at,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Bearer token is required")
    settings = get_settings()
    payload = decode_access_token(credentials.credentials, settings=settings)
    username = str(payload.get("sub") or "").strip()
    role = str(payload.get("role") or "").strip()
    if not username or not role:
        raise AuthenticationError("Invalid token payload")
    return CurrentUser(username=username, role=role)


def require_superadmin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin role required")
    return user


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role not in {"admin", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def create_app() -> FastAPI:
    settings = get_settings()
    service = get_service()

    app = FastAPI(title="Telegram SOCKS5 API", version="0.1.0")
    media_dir = _find_media_dir()

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    if media_dir:
        app.mount("/media", StaticFiles(directory=media_dir), name="media")

    @app.exception_handler(AppError)
    async def app_error_handler(_request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.get("/health", response_model=HealthResponse)
    def health():
        state = service.storage.load_state()
        return HealthResponse(
            status="ok",
            service=settings.service_name,
            proxy_users=len(state.proxy_users),
            admins=len(state.admins),
        )

    @app.get("/", include_in_schema=False)
    def admin_panel():
        return FileResponse(STATIC_DIR / "index.html")

    @app.on_event("startup")
    def startup() -> None:
        settings.ensure_dirs()
        service.ensure_runtime()

    @app.post("/auth/login", response_model=TokenResponse)
    def login(payload: LoginRequest):
        username, role = service.login(payload.username, payload.password)
        token = create_access_token(settings=settings, subject=username, role=role)
        return TokenResponse(access_token=token, username=username, role=role)

    @app.get("/proxy-users", response_model=list[ProxyUserOut])
    def list_proxy_users(_user: CurrentUser = Depends(require_admin)):
        return [_to_proxy_user_out(row) for row in service.list_proxy_users()]

    @app.post("/proxy-users", response_model=ProxyUserOut, status_code=status.HTTP_201_CREATED)
    def create_proxy_user(payload: ProxyUserCreate, user: CurrentUser = Depends(require_admin)):
        row = service.create_proxy_user(
            payload.username,
            payload.password,
            enabled=payload.enabled,
            current_role=user.role,
        )
        return _to_proxy_user_out(row)

    @app.patch("/proxy-users/{username}", response_model=ProxyUserOut)
    def update_proxy_user(username: str, payload: ProxyUserUpdate, user: CurrentUser = Depends(require_admin)):
        row = service.update_proxy_user(
            username,
            password=payload.password,
            enabled=payload.enabled,
            current_role=user.role,
        )
        return _to_proxy_user_out(row)

    @app.delete("/proxy-users/{username}", response_model=MessageResponse)
    def delete_proxy_user(username: str, user: CurrentUser = Depends(require_admin)):
        service.delete_proxy_user(username, current_role=user.role)
        return MessageResponse(message="Proxy user deleted")

    @app.get("/admins", response_model=list[AdminOut])
    def list_admins(_user: CurrentUser = Depends(require_superadmin)):
        return [_to_admin_out(row) for row in service.list_admins()]

    @app.post("/admins", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
    def create_admin(payload: AdminCreate, user: CurrentUser = Depends(require_superadmin)):
        row = service.create_admin(payload.username, payload.password, current_role=user.role)
        return _to_admin_out(row)

    @app.patch("/admins/{username}/password", response_model=AdminOut)
    def update_admin_password(username: str, payload: AdminPasswordUpdate, user: CurrentUser = Depends(require_superadmin)):
        row = service.update_admin_password(username, payload.password, current_role=user.role)
        return _to_admin_out(row)

    @app.delete("/admins/{username}", response_model=MessageResponse)
    def delete_admin(username: str, user: CurrentUser = Depends(require_superadmin)):
        service.delete_admin(username, current_role=user.role)
        return MessageResponse(message="Admin deleted")

    return app


app = create_app()
