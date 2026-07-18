from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Permission(StrEnum):
    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DEACTIVATE = "users.deactivate"
    ROLES_READ = "roles.read"
    ROLES_ASSIGN = "roles.assign"
    SESSIONS_REVOKE = "sessions.revoke"
    SOURCES_REVIEW = "sources.review"
    DATASETS_REVIEW = "datasets.review"
    DATASETS_APPROVE = "datasets.approve"
    DATASETS_EXPORT = "datasets.export"
    TRAINING_CONFIGURE = "training.configure"
    TRAINING_START = "training.start"
    TRAINING_CANCEL = "training.cancel"
    TRAINING_RESUME = "training.resume"
    EVALUATIONS_START = "evaluations.start"
    EVALUATIONS_READ = "evaluations.read"
    CANDIDATES_CREATE = "candidates.create"
    CANDIDATES_REVIEW = "candidates.review"
    CANDIDATES_SECURITY_APPROVE = "candidates.security_approve"
    CANDIDATES_STAGE_APPROVE = "candidates.stage_approve"
    STAGING_EXECUTE = "staging.execute"
    STAGING_ROLLBACK = "staging.rollback"
    AUDIT_READ = "audit.read"
    GOVERNANCE_MANAGE = "governance.manage"
    EMERGENCY_REVOKE = "emergency.revoke"


class RoleName(StrEnum):
    SUPER_ADMIN = "super_admin"
    AI_ENGINEER = "ai_engineer"
    DATA_REVIEWER = "data_reviewer"
    SECURITY_REVIEWER = "security_reviewer"
    MODEL_APPROVER = "model_approver"
    OPERATOR = "operator"
    VIEWER = "viewer"


ROLE_PERMISSIONS: dict[RoleName, set[Permission]] = {
    RoleName.SUPER_ADMIN: set(Permission),
    RoleName.AI_ENGINEER: {
        Permission.SOURCES_REVIEW,
        Permission.TRAINING_CONFIGURE,
        Permission.TRAINING_START,
        Permission.TRAINING_CANCEL,
        Permission.TRAINING_RESUME,
        Permission.EVALUATIONS_START,
        Permission.EVALUATIONS_READ,
        Permission.CANDIDATES_CREATE,
        Permission.CANDIDATES_REVIEW,
    },
    RoleName.DATA_REVIEWER: {
        Permission.SOURCES_REVIEW,
        Permission.DATASETS_REVIEW,
        Permission.DATASETS_APPROVE,
        Permission.DATASETS_EXPORT,
        Permission.EVALUATIONS_READ,
    },
    RoleName.SECURITY_REVIEWER: {
        Permission.EVALUATIONS_READ,
        Permission.CANDIDATES_SECURITY_APPROVE,
        Permission.CANDIDATES_REVIEW,
        Permission.AUDIT_READ,
    },
    RoleName.MODEL_APPROVER: {
        Permission.EVALUATIONS_READ,
        Permission.CANDIDATES_REVIEW,
        Permission.CANDIDATES_STAGE_APPROVE,
    },
    RoleName.OPERATOR: {
        Permission.TRAINING_START,
        Permission.TRAINING_CANCEL,
        Permission.TRAINING_RESUME,
        Permission.STAGING_EXECUTE,
        Permission.STAGING_ROLLBACK,
        Permission.EVALUATIONS_READ,
    },
    RoleName.VIEWER: {
        Permission.ROLES_READ,
        Permission.EVALUATIONS_READ,
    },
}


class User(BaseModel):
    user_id: str
    email: EmailStr
    normalized_email: str
    username: str
    display_name: str
    password_hash: str
    active: bool = True
    locked_until: datetime | None = None
    failed_login_count: int = 0
    last_login_at: datetime | None = None
    password_changed_at: datetime | None = None
    session_revocation_version: int = 0
    created_at: datetime
    updated_at: datetime


class PublicUser(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    display_name: str
    active: bool
    roles: list[RoleName]
    permissions: list[Permission]


class AuthSession(BaseModel):
    session_id: str
    user_id: str
    refresh_family_id: str
    refresh_token_hash: str
    refresh_token_id: str
    user_agent: str | None = None
    ip_address: str | None = None
    revoked: bool = False
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class RefreshTokenFamily(BaseModel):
    family_id: str
    user_id: str
    revoked: bool = False
    created_at: datetime
    updated_at: datetime


class LoginAttempt(BaseModel):
    attempt_id: str
    normalized_email: str
    success: bool
    ip_address: str | None = None
    created_at: datetime


class SecurityEvent(BaseModel):
    event_id: str
    severity: str
    event_type: str
    actor_user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuditEvent(BaseModel):
    event_id: str
    actor_user_id: str | None
    actor_session_id: str | None
    actor_roles: list[str] = Field(default_factory=list)
    actor_permissions: list[str] = Field(default_factory=list)
    action: str
    resource_type: str
    resource_id: str | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    result: str
    reason: str | None = None
    risk_level: str = "low"
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    correlation_id: str | None = None
    created_at: datetime


class AuthenticatedPrincipal(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user: User
    roles: list[RoleName]
    permissions: set[Permission]
    session_id: str
    token_id: str


class CreateUserInput(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    password: str
    roles: list[RoleName] = Field(default_factory=lambda: [RoleName.VIEWER])

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password_strength(password: str) -> None:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long")
    checks = (
        any(char.islower() for char in password),
        any(char.isupper() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    )
    if sum(checks) < 3:
        raise ValueError("Password must include at least three character classes")
