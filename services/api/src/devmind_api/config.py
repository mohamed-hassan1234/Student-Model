from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
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
    embedding_dimensions: int = Field(default=16, ge=1, le=4096, alias="EMBEDDING_DIMENSIONS")
    vector_search_provider: str = Field(default="mock", alias="VECTOR_SEARCH_PROVIDER")
    model_provider_timeout_seconds: int = Field(
        default=20, ge=1, le=180, alias="MODEL_PROVIDER_TIMEOUT_SECONDS"
    )
    learning_cycle_max_examples: int = Field(
        default=20, ge=1, le=500, alias="LEARNING_CYCLE_MAX_EXAMPLES"
    )
    learning_cycle_max_provider_calls: int = Field(
        default=40, ge=1, le=1000, alias="LEARNING_CYCLE_MAX_PROVIDER_CALLS"
    )
    teacher_provider: str = Field(default="mock", alias="TEACHER_PROVIDER")
    teacher_model_name: str = Field(default="mock-devmind-teacher", alias="TEACHER_MODEL_NAME")
    safe_code_runner_enabled: bool = Field(default=False, alias="SAFE_CODE_RUNNER_ENABLED")
    training_artifact_directory: Path = Field(
        default=Path("storage/generated/training"), alias="TRAINING_ARTIFACT_DIRECTORY"
    )
    training_max_runtime_minutes: int = Field(
        default=60, ge=1, le=10080, alias="TRAINING_MAX_RUNTIME_MINUTES"
    )
    training_allow_remote_code: bool = Field(default=False, alias="TRAINING_ALLOW_REMOTE_CODE")
    training_default_seed: int = Field(default=7, ge=0, alias="TRAINING_DEFAULT_SEED")
    auth_jwt_secret: str | None = Field(default=None, alias="AUTH_JWT_SECRET")
    auth_jwt_issuer: str = Field(default="devmind-ai-local", alias="AUTH_JWT_ISSUER")
    auth_jwt_audience: str = Field(default="devmind-ai-api", alias="AUTH_JWT_AUDIENCE")
    auth_access_token_minutes: int = Field(
        default=15, ge=1, le=120, alias="AUTH_ACCESS_TOKEN_MINUTES"
    )
    auth_refresh_token_minutes: int = Field(
        default=10080, ge=5, le=43200, alias="AUTH_REFRESH_TOKEN_MINUTES"
    )
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_failed_login_threshold: int = Field(
        default=5, ge=1, le=20, alias="AUTH_FAILED_LOGIN_THRESHOLD"
    )
    auth_lockout_minutes: int = Field(default=15, ge=1, le=1440, alias="AUTH_LOCKOUT_MINUTES")
    auth_strict_governance_enabled: bool = Field(
        default=True, alias="AUTH_STRICT_GOVERNANCE_ENABLED"
    )
    ingestion_chunk_size: int = Field(default=1200, ge=200, le=8000, alias="INGESTION_CHUNK_SIZE")
    ingestion_chunk_overlap: int = Field(
        default=120, ge=0, le=2000, alias="INGESTION_CHUNK_OVERLAP"
    )
    max_upload_bytes: int = Field(default=5_242_880, ge=1024, alias="MAX_UPLOAD_BYTES")
    max_web_fetch_bytes: int = Field(default=2_097_152, ge=1024, alias="MAX_WEB_FETCH_BYTES")
    max_web_redirects: int = Field(default=3, ge=0, le=10, alias="MAX_WEB_REDIRECTS")
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

    @field_validator("ingestion_chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Chunk overlap must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_auth_browser_defaults(self) -> "Settings":
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed with credentialed auth")
        if self.app_env.lower() in {"production", "prod"} and not self.auth_cookie_secure:
            raise ValueError("Secure authentication cookies are required in production")
        return self

    def redacted(self) -> dict[str, object]:
        data = self.model_dump(mode="json")
        for key in list(data):
            if any(token in key.lower() for token in ("uri", "secret", "password", "token", "key")):
                data[key] = "[redacted]"
        return data


@lru_cache
def get_settings() -> Settings:
    return Settings()
