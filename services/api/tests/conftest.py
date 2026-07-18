from collections.abc import AsyncIterator

import pytest
from fakes import FakeMongoDatabase
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from devmind_api.auth.models import CreateUserInput, RoleName
from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.services import AuthService
from devmind_api.config import Settings, get_settings
from devmind_api.db import get_database
from devmind_api.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        MONGODB_URI="mongodb://example.invalid:27017",
        MONGODB_DATABASE="devmind_test",
        MONGODB_TEST_DATABASE="devmind_test",
        CORS_ORIGINS="http://example.test",
    )


@pytest.fixture
def app(test_settings: Settings, fake_database: FakeMongoDatabase) -> FastAPI:
    get_settings.cache_clear()
    application = create_app(test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_database] = lambda: fake_database
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def fake_database() -> FakeMongoDatabase:
    return FakeMongoDatabase()


@pytest.fixture
async def admin_headers(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> dict[str, str]:
    service = AuthService(AuthRepository(fake_database), test_settings)
    user = await service.create_user(
        CreateUserInput(
            email="admin@example.com",
            username="admin",
            display_name="Admin",
            roles=[RoleName.SUPER_ADMIN],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    tokens = await service.login(str(user.email), "StrongPassword123!")
    return {"Authorization": f"Bearer {tokens['access_token']}"}
