from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, ge=1, le=65535, alias="API_PORT")
    frontend_url: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_URL")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )
    mongodb_uri: str = Field(default="mongodb://127.0.0.1:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="devmind_local", alias="MONGODB_DATABASE")
    mongodb_test_database: str = Field(default="devmind_test", alias="MONGODB_TEST_DATABASE")
    mongodb_connect_timeout_ms: int = Field(
        default=2000, ge=100, le=30000, alias="MONGODB_CONNECT_TIMEOUT_MS"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    worker_enabled: bool = Field(default=False, alias="WORKER_ENABLED")
    local_model_provider: str = Field(default="mock", alias="LOCAL_MODEL_PROVIDER")
    local_model_base_url: str = Field(
        default="http://127.0.0.1:11434", alias="LOCAL_MODEL_BASE_URL"
    )
    local_model_name: str = Field(default="mock-devmind-local", alias="LOCAL_MODEL_NAME")
    embedding_provider: str = Field(default="mock", alias="EMBEDDING_PROVIDER")
    embedding_model_name: str = Field(default="mock-embedding", alias="EMBEDDING_MODEL_NAME")
    storage_directory: Path = Field(default=Path("storage"), alias="STORAGE_DIRECTORY")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("CORS_ORIGINS must be a comma-separated string or list")

    @field_validator("mongodb_database", "mongodb_test_database")
    @classmethod
    def validate_database_name(cls, value: str) -> str:
        unsafe = {"admin", "config", "local", "production", "prod"}
        if not value or value.lower() in unsafe:
            raise ValueError("MongoDB database name is missing or unsafe")
        if any(char in value for char in ['"', " ", "$", "/", "\\", "."]):
            raise ValueError("MongoDB database name contains unsupported characters")
        return value

    def redacted(self) -> dict[str, object]:
        data = self.model_dump(mode="json")
        for key in list(data):
            if any(token in key.lower() for token in ("uri", "secret", "password", "token", "key")):
                data[key] = "[redacted]"
        return data


@lru_cache
def get_settings() -> Settings:
    return Settings()
