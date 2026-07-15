import os

import pytest

from devmind_api.config import Settings


def safe_test_database_name(name: str) -> bool:
    return name.startswith("devmind_test") and name not in {"devmind", "devmind_local"}


@pytest.mark.mongodb
def test_mongodb_integration_requires_explicit_safe_database() -> None:
    uri = os.getenv("MONGODB_TEST_URI")
    database = os.getenv("MONGODB_TEST_DATABASE", "devmind_test")
    if not uri:
        pytest.skip("MONGODB_TEST_URI is not configured; real MongoDB integration tests skipped.")

    assert safe_test_database_name(database)
    settings = Settings(MONGODB_URI=uri, MONGODB_DATABASE=database, MONGODB_TEST_DATABASE=database)
    assert settings.mongodb_database == database
