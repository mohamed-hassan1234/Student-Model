from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette import status

from devmind_api.auth.dependencies import PrincipalDep, require_permission
from devmind_api.auth.models import Permission
from devmind_api.db import MongoDatabase, get_database
from devmind_api.exceptions import DevMindError
from devmind_api.governance.models import ApprovalDecisionType
from devmind_api.governance.repositories import GovernanceRepository
from devmind_api.governance.services import (
    GovernanceConflictError,
    GovernanceService,
    GovernanceServiceError,
)
from devmind_api.technology.training_repositories import TrainingRepository

router = APIRouter(prefix="/governance", tags=["governance"])
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


class CreateApprovalRequestBody(BaseModel):
    candidate_id: str = Field(min_length=2, max_length=160)
    reason: str = Field(min_length=5, max_length=2000)


class ApprovalDecisionBody(BaseModel):
    decision_type: ApprovalDecisionType
    approved: bool
    notes: str | None = Field(default=None, max_length=2000)


class CreateStagingRequestBody(BaseModel):
    candidate_id: str = Field(min_length=2, max_length=160)
    approval_request_id: str = Field(min_length=2, max_length=160)
    staging_environment: str = Field(default="manual_staging", max_length=120)
    reason: str = Field(min_length=5, max_length=2000)


class RollbackBody(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class ReasonBody(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


def get_governance_service(database: DatabaseDep) -> GovernanceService:
    return GovernanceService(GovernanceRepository(database), TrainingRepository(database))


GovernanceDep = Annotated[GovernanceService, Depends(get_governance_service)]


@router.get("/policies")
async def list_governance_policies(
    service: GovernanceDep,
    _: Annotated[Any, Depends(require_permission(Permission.GOVERNANCE_MANAGE))],
) -> Any:
    return {"policies": await service.ensure_default_policies()}


@router.post("/approval-requests", status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    request_body: CreateApprovalRequestBody,
    principal: Annotated[Any, Depends(require_permission(Permission.CANDIDATES_REVIEW))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.create_approval_request(
            request_body.candidate_id, request_body.reason, principal
        )
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/approval-requests")
async def list_approval_requests(
    database: DatabaseDep,
    _: Annotated[Any, Depends(require_permission(Permission.CANDIDATES_REVIEW))],
) -> Any:
    return {"approval_requests": await GovernanceRepository(database).list_approval_requests()}


@router.get("/approval-requests/{approval_request_id}")
async def read_approval_request(
    approval_request_id: str,
    database: DatabaseDep,
    _: Annotated[Any, Depends(require_permission(Permission.CANDIDATES_REVIEW))],
) -> Any:
    request = await GovernanceRepository(database).get_approval_request(approval_request_id)
    if request is None:
        raise DevMindError("Approval request not found", status.HTTP_404_NOT_FOUND)
    decisions = await GovernanceRepository(database).list_decisions(approval_request_id)
    return {"request": request, "decisions": decisions}


@router.post("/approval-requests/{approval_request_id}/decisions")
async def decide_approval_request(
    approval_request_id: str,
    request_body: ApprovalDecisionBody,
    principal: PrincipalDep,
    service: GovernanceDep,
) -> Any:
    permission = (
        Permission.CANDIDATES_SECURITY_APPROVE
        if request_body.decision_type == ApprovalDecisionType.SECURITY
        else Permission.CANDIDATES_STAGE_APPROVE
    )
    if permission not in principal.permissions:
        raise DevMindError("Permission denied", status.HTTP_403_FORBIDDEN)
    try:
        return await service.decide(
            approval_request_id,
            request_body.decision_type,
            request_body.approved,
            request_body.notes,
            principal,
        )
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/approval-requests/{approval_request_id}/cancel")
async def cancel_approval_request(
    approval_request_id: str,
    request_body: ReasonBody,
    principal: Annotated[Any, Depends(require_permission(Permission.CANDIDATES_REVIEW))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.cancel_approval_request(
            approval_request_id, request_body.reason, principal
        )
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/approval-requests/{approval_request_id}/emergency-override")
async def emergency_override_approval_request(
    approval_request_id: str,
    request_body: ReasonBody,
    principal: Annotated[Any, Depends(require_permission(Permission.EMERGENCY_REVOKE))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.emergency_override(approval_request_id, request_body.reason, principal)
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/staging-requests", status_code=status.HTTP_201_CREATED)
async def create_staging_request(
    request_body: CreateStagingRequestBody,
    principal: Annotated[Any, Depends(require_permission(Permission.STAGING_EXECUTE))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.create_staging_request(
            candidate_id=request_body.candidate_id,
            approval_request_id=request_body.approval_request_id,
            staging_environment=request_body.staging_environment,
            reason=request_body.reason,
            actor=principal,
        )
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/staging-requests")
async def list_staging_requests(
    database: DatabaseDep,
    _: Annotated[Any, Depends(require_permission(Permission.STAGING_EXECUTE))],
) -> Any:
    return {"staging_requests": await GovernanceRepository(database).list_staging_requests()}


@router.post("/staging-requests/{staging_request_id}/record-assignment")
async def record_manual_assignment(
    staging_request_id: str,
    principal: Annotated[Any, Depends(require_permission(Permission.STAGING_EXECUTE))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.record_manual_assignment(staging_request_id, principal)
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/staging-requests/{staging_request_id}/rollback")
async def rollback_staging_request(
    staging_request_id: str,
    request_body: RollbackBody,
    principal: Annotated[Any, Depends(require_permission(Permission.STAGING_ROLLBACK))],
    service: GovernanceDep,
) -> Any:
    try:
        return await service.rollback_staging_request(
            staging_request_id, request_body.reason, principal
        )
    except GovernanceConflictError as exc:
        raise DevMindError(str(exc), status.HTTP_409_CONFLICT) from exc
    except GovernanceServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc
