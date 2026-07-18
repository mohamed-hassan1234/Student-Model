from datetime import timedelta

import pytest
from fakes import FakeMongoDatabase
from httpx import AsyncClient

from devmind_api.auth.models import CreateUserInput, RoleName
from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.security import AuthSecurityError, ensure_signing_secret
from devmind_api.auth.services import AuthService
from devmind_api.config import Settings
from devmind_shared.time import utc_now

pytestmark = pytest.mark.anyio


async def test_auth_login_refresh_and_me(
    client: AsyncClient, fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    service = AuthService(AuthRepository(fake_database), test_settings)
    await service.create_user(
        CreateUserInput(
            email="user@example.com",
            username="phase4user",
            display_name="Phase 4 User",
            roles=[RoleName.VIEWER],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login.json()["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != access_token


async def test_permission_denial_is_403(
    client: AsyncClient, fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    service = AuthService(AuthRepository(fake_database), test_settings)
    user = await service.create_user(
        CreateUserInput(
            email="viewer@example.com",
            username="viewer",
            display_name="Viewer",
            roles=[RoleName.VIEWER],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    tokens = await service.login(str(user.email), "StrongPassword123!")

    response = await client.post(
        "/api/v1/technology/training/hardware/inspect",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Permission denied"


def test_jwt_secret_rejects_example_placeholder(test_settings: Settings) -> None:
    settings = test_settings.model_copy(
        update={
            "app_env": "local",
            "auth_jwt_secret": "<set-a-local-random-secret-at-least-32-characters>",
        }
    )

    with pytest.raises(AuthSecurityError):
        ensure_signing_secret(settings)


async def test_refresh_reuse_revokes_refresh_family(
    client: AsyncClient, fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    service = AuthService(AuthRepository(fake_database), test_settings)
    user = await service.create_user(
        CreateUserInput(
            email="reuse@example.com",
            username="reuseuser",
            display_name="Reuse User",
            roles=[RoleName.VIEWER],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    tokens = await service.login(str(user.email), "StrongPassword123!")
    first_refresh = str(tokens["refresh_token"])

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200

    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401

    session = await AuthRepository(fake_database).get_session(str(tokens["session_id"]))
    assert session is not None
    assert session.revoked is True
    family = await AuthRepository(fake_database).get_refresh_family(session.refresh_family_id)
    assert family is not None
    assert family.revoked is True


async def test_expired_session_rejects_access_token(
    client: AsyncClient, fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    service = AuthService(AuthRepository(fake_database), test_settings)
    user = await service.create_user(
        CreateUserInput(
            email="expired@example.com",
            username="expireduser",
            display_name="Expired User",
            roles=[RoleName.VIEWER],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    tokens = await service.login(str(user.email), "StrongPassword123!")
    await AuthRepository(fake_database).update_session(
        str(tokens["session_id"]), {"expires_at": utc_now() - timedelta(minutes=1)}
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 401


async def test_deactivated_user_cannot_login(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    service = AuthService(AuthRepository(fake_database), test_settings)
    user = await service.create_user(
        CreateUserInput(
            email="disabled@example.com",
            username="disableduser",
            display_name="Disabled User",
            roles=[RoleName.VIEWER],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    await AuthRepository(fake_database).update_user(user.user_id, {"active": False})

    with pytest.raises(Exception, match="Invalid username or password"):
        await service.login(str(user.email), "StrongPassword123!")
