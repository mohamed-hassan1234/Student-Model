import pytest
from pydantic import ValidationError

from devmind_api.config import Settings


def test_cors_origins_parse_from_csv() -> None:
    settings = Settings(CORS_ORIGINS="http://one.test, http://two.test")

    assert settings.cors_origins == ["http://one.test", "http://two.test"]


def test_unsafe_database_name_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(MONGODB_DATABASE="admin")


def test_redacted_settings_hide_sensitive_values() -> None:
    settings = Settings(MONGODB_URI="mongodb://user:password@example.test/devmind")

    redacted = settings.redacted()

    assert redacted["mongodb_uri"] == "[redacted]"
    assert "password" not in str(redacted)
