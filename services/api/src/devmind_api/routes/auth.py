from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, Request, Response
from pydantic import BaseModel, EmailStr, Field
from starlette import status

from devmind_api.auth.dependencies import AuthServiceDep, PrincipalDep, require_permission
from devmind_api.auth.models import (
    ROLE_PERMISSIONS,
    CreateUserInput,
    Permission,
    PublicUser,
    RoleName,
)
from devmind_api.auth.services import AuthServiceError
from devmind_api.config import Settings, get_settings
from devmind_api.exceptions import DevMindError

router = APIRouter(prefix="/auth", tags=["auth"])
SettingsDep = Annotated[Settings, Depends(get_settings)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=4096)


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type label, not a secret.
    expires_in: int
    csrf_token: str
    session_id: str
    user: PublicUser


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=4096)
    new_password: str = Field(min_length=12, max_length=4096)


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=4096)


class SetActiveRequest(BaseModel):
    active: bool


class RoleAssignmentRequest(BaseModel):
    role: RoleName


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _set_auth_cookies(response: Response, settings: Settings, payload: dict[str, Any]) -> None:
    secure = settings.auth_cookie_secure
    max_age = settings.auth_refresh_token_minutes * 60
    response.set_cookie(
        "devmind_refresh",
        str(payload["refresh_token"]),
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )
    response.set_cookie(
        "devmind_csrf",
        str(payload["csrf_token"]),
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    secure = settings.auth_cookie_secure
    for name in ("devmind_refresh", "devmind_csrf", "devmind_access"):
        response.delete_cookie(name, secure=secure, samesite="lax", path="/api/v1/auth")


async def _token_response(
    payload: dict[str, Any],
    auth: AuthServiceDep,
    response: Response,
    settings: SettingsDep,
) -> TokenResponse:
    user = await auth.authenticate_access_token(str(payload["access_token"]))
    _set_auth_cookies(response, settings, payload)
    return TokenResponse(
        access_token=str(payload["access_token"]),
        refresh_token=str(payload["refresh_token"]),
        expires_in=int(payload["expires_in"]),
        csrf_token=str(payload["csrf_token"]),
        session_id=str(payload["session_id"]),
        user=await auth.public_user(user.user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request_body: LoginRequest,
    request: Request,
    response: Response,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> TokenResponse:
    try:
        payload = await auth.login(
            str(request_body.email),
            request_body.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=_client_ip(request),
        )
        return await _token_response(payload, auth, response, settings)
    except (AuthServiceError, ValueError) as exc:
        raise DevMindError(str(exc), status.HTTP_401_UNAUTHORIZED) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    auth: AuthServiceDep,
    settings: SettingsDep,
    request_body: Annotated[RefreshRequest | None, Body()] = None,
    x_csrf_token: Annotated[str | None, Header(alias="x-csrf-token")] = None,
) -> TokenResponse:
    body_refresh = request_body.refresh_token if request_body else None
    refresh_token = body_refresh or request.cookies.get("devmind_refresh")
    if not refresh_token:
        raise DevMindError("Refresh token is required", status.HTTP_401_UNAUTHORIZED)
    if body_refresh is None:
        cookie_csrf = request.cookies.get("devmind_csrf")
        if not cookie_csrf or x_csrf_token != cookie_csrf:
            raise DevMindError("CSRF token is required", status.HTTP_403_FORBIDDEN)
    try:
        payload = await auth.refresh(refresh_token)
        return await _token_response(payload, auth, response, settings)
    except (AuthServiceError, ValueError) as exc:
        _clear_auth_cookies(response, settings)
        raise DevMindError(str(exc), status.HTTP_401_UNAUTHORIZED) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    principal: PrincipalDep,
    response: Response,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> None:
    await auth.logout(principal)
    _clear_auth_cookies(response, settings)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    principal: PrincipalDep,
    response: Response,
    auth: AuthServiceDep,
    settings: SettingsDep,
) -> None:
    await auth.logout_all(principal)
    _clear_auth_cookies(response, settings)


@router.get("/me", response_model=PublicUser)
async def read_me(principal: PrincipalDep, auth: AuthServiceDep) -> PublicUser:
    return await auth.public_user(principal.user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request_body: ChangePasswordRequest,
    principal: PrincipalDep,
    auth: AuthServiceDep,
) -> None:
    try:
        await auth.change_password(
            principal, request_body.current_password, request_body.new_password
        )
    except (AuthServiceError, ValueError) as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/permissions")
async def list_permissions(
    _: Annotated[Any, Depends(require_permission(Permission.ROLES_READ))],
) -> dict[str, Any]:
    return {
        "permissions": [permission.value for permission in Permission],
        "roles": {
            role.value: sorted(permission.value for permission in permissions)
            for role, permissions in ROLE_PERMISSIONS.items()
        },
    }


@router.post("/users", response_model=PublicUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    request_body: CreateUserInput,
    principal: Annotated[Any, Depends(require_permission(Permission.USERS_CREATE))],
    auth: AuthServiceDep,
) -> PublicUser:
    try:
        user = await auth.create_user(request_body, principal)
        return await auth.public_user(user)
    except (AuthServiceError, ValueError) as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/users")
async def list_users(
    principal: Annotated[Any, Depends(require_permission(Permission.USERS_READ))],
    auth: AuthServiceDep,
) -> dict[str, list[PublicUser]]:
    return {"users": await auth.list_public_users(principal)}


@router.post("/users/{user_id}/roles", response_model=PublicUser)
async def assign_role(
    user_id: str,
    request_body: RoleAssignmentRequest,
    principal: Annotated[Any, Depends(require_permission(Permission.ROLES_ASSIGN))],
    auth: AuthServiceDep,
) -> PublicUser:
    try:
        return await auth.assign_role(principal, user_id, request_body.role)
    except AuthServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.delete("/users/{user_id}/roles/{role}", response_model=PublicUser)
async def remove_role(
    user_id: str,
    role: RoleName,
    principal: Annotated[Any, Depends(require_permission(Permission.ROLES_ASSIGN))],
    auth: AuthServiceDep,
) -> PublicUser:
    try:
        return await auth.remove_role(principal, user_id, role)
    except AuthServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/users/{user_id}/active", response_model=PublicUser)
async def set_user_active(
    user_id: str,
    request_body: SetActiveRequest,
    principal: Annotated[Any, Depends(require_permission(Permission.USERS_DEACTIVATE))],
    auth: AuthServiceDep,
) -> PublicUser:
    try:
        user = await auth.set_active(principal, user_id, request_body.active)
        return await auth.public_user(user)
    except AuthServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: str,
    request_body: ResetPasswordRequest,
    principal: Annotated[Any, Depends(require_permission(Permission.USERS_UPDATE))],
    auth: AuthServiceDep,
) -> None:
    try:
        await auth.reset_password(principal, user_id, request_body.new_password)
    except (AuthServiceError, ValueError) as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/users/{user_id}/revoke-sessions", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_sessions(
    user_id: str,
    principal: Annotated[Any, Depends(require_permission(Permission.SESSIONS_REVOKE))],
    auth: AuthServiceDep,
) -> None:
    try:
        await auth.revoke_sessions(principal, user_id)
    except AuthServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_404_NOT_FOUND) from exc
