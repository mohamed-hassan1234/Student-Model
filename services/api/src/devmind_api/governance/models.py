from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ApprovalRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class ApprovalDecisionType(StrEnum):
    MODEL = "model"
    SECURITY = "security"


class StagingRequestStatus(StrEnum):
    PENDING = "pending"
    READY_FOR_MANUAL_STAGING = "ready_for_manual_staging"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    ASSIGNMENT_RECORDED = "assignment_recorded"


class GovernancePolicy(BaseModel):
    policy_id: str
    name: str
    description: str
    enabled: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    approval_request_id: str
    candidate_id: str
    requested_by: str
    status: ApprovalRequestStatus = ApprovalRequestStatus.PENDING
    reason: str
    required_decisions: list[ApprovalDecisionType] = Field(
        default_factory=lambda: [ApprovalDecisionType.MODEL, ApprovalDecisionType.SECURITY]
    )
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApprovalDecision(BaseModel):
    decision_id: str
    approval_request_id: str
    candidate_id: str
    reviewer_id: str
    reviewer_roles: list[str]
    decision_type: ApprovalDecisionType
    approved: bool
    notes: str | None = None
    created_at: datetime


class StagingRequest(BaseModel):
    staging_request_id: str
    candidate_id: str
    approval_request_id: str
    requested_by: str
    status: StagingRequestStatus
    staging_environment: str
    adapter_hash: str
    reason: str
    created_at: datetime
    updated_at: datetime


class StagingEvent(BaseModel):
    event_id: str
    staging_request_id: str
    candidate_id: str
    actor_user_id: str
    event_type: str
    result: str
    reason: str | None = None
    risk_level: str = "low"
    created_at: datetime


class ProductionModelAssignment(BaseModel):
    assignment_id: str
    environment: str
    candidate_id: str
    adapter_hash: str
    assigned_by: str
    active: bool
    created_at: datetime


def governance_document(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python")
