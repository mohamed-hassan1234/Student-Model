from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from devmind_api.auth.models import AuthenticatedPrincipal, Permission
from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.services import AuthService, AuthServiceError
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoDatabase, get_database
from devmind_api.exceptions import DevMindError

bearer = HTTPBearer(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


def get_auth_service(database: DatabaseDep, settings: SettingsDep) -> AuthService:
    return AuthService(AuthRepository(database), settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_principal(
    request: Request,
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)] = None,
) -> AuthenticatedPrincipal:
    token = credentials.credentials if credentials else request.cookies.get("devmind_access")
    if not token:
        raise DevMindError("Authentication is required", status.HTTP_401_UNAUTHORIZED)
    try:
        return await auth.authenticate_access_token(token)
    except AuthServiceError as exc:
        raise DevMindError("Authentication is required", status.HTTP_401_UNAUTHORIZED) from exc


PrincipalDep = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]


def require_permission(
    permission: Permission,
) -> Callable[..., Awaitable[AuthenticatedPrincipal]]:
    async def dependency(
        principal: PrincipalDep,
        auth: AuthServiceDep,
    ) -> AuthenticatedPrincipal:
        if permission not in principal.permissions:
            await auth.security_event(
                "unauthorized_permission_attempt",
                "medium",
                actor_user_id=principal.user.user_id,
                reason=permission.value,
            )
            raise DevMindError("Permission denied", status.HTTP_403_FORBIDDEN)
        return principal

    return dependency
