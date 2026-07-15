from collections.abc import AsyncIterator

import pytest
from fakes import FakeMongoDatabase
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

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
def app(test_settings: Settings) -> FastAPI:
    get_settings.cache_clear()
    fake_database = FakeMongoDatabase()
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
