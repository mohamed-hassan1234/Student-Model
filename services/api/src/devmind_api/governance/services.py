from datetime import timedelta

from devmind_api.auth.models import AuthenticatedPrincipal, Permission, RoleName
from devmind_api.auth.security import new_secret_token
from devmind_api.governance.models import (
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalRequest,
    ApprovalRequestStatus,
    GovernancePolicy,
    ProductionModelAssignment,
    StagingEvent,
    StagingRequest,
    StagingRequestStatus,
)
from devmind_api.governance.repositories import GovernanceRepository
from devmind_api.technology.hashing import stable_id
from devmind_api.technology.training_models import (
    DeploymentRecommendationStatus,
    ManifestReviewStatus,
)
from devmind_api.technology.training_repositories import TrainingRepository
from devmind_shared.time import utc_now


class GovernanceServiceError(Exception):
    pass


class GovernanceConflictError(GovernanceServiceError):
    pass


class GovernanceService:
    def __init__(
        self,
        repository: GovernanceRepository,
        training_repository: TrainingRepository,
    ) -> None:
        self._repository = repository
        self._training_repository = training_repository

    async def ensure_default_policies(self) -> list[GovernancePolicy]:
        now = utc_now()
        policy = GovernancePolicy(
            policy_id="policy_manual_model_staging_v1",
            name="Manual model staging",
            description=(
                "Model candidates require model and security approval from distinct reviewers "
                "before any manual staging request can be marked ready."
            ),
            rules={
                "requires_distinct_reviewers": True,
                "required_decisions": ["model", "security"],
                "automatic_deployment_allowed": False,
            },
            created_at=now,
            updated_at=now,
        )
        await self._repository.save_policy(policy)
        return await self._repository.list_policies()

    async def create_approval_request(
        self, candidate_id: str, reason: str, actor: AuthenticatedPrincipal
    ) -> ApprovalRequest:
        candidate = await self._training_repository.get_phase3_model_candidate(candidate_id)
        if candidate is None:
            raise GovernanceServiceError("Model candidate not found")
        now = utc_now()
        request = ApprovalRequest(
            approval_request_id=stable_id(
                "appr",
                f"{candidate_id}:{actor.user.user_id}:{now.isoformat()}:{new_secret_token()}",
            ),
            candidate_id=candidate_id,
            requested_by=actor.user.user_id,
            reason=reason,
            expires_at=now + timedelta(days=7),
            created_at=now,
            updated_at=now,
        )
        created = await self._repository.create_approval_request(request)
        await self._record_audit(
            actor,
            "governance.approval_request.create",
            "approval_request",
            created.approval_request_id,
            "success",
            reason,
            "medium",
        )
        return created

    async def decide(
        self,
        approval_request_id: str,
        decision_type: ApprovalDecisionType,
        approved: bool,
        notes: str | None,
        actor: AuthenticatedPrincipal,
    ) -> dict[str, object]:
        request = await self._repository.get_approval_request(approval_request_id)
        if request is None:
            raise GovernanceServiceError("Approval request not found")
        if request.status != ApprovalRequestStatus.PENDING:
            raise GovernanceConflictError("Approval request is not pending")
        now = utc_now()
        if request.expires_at is not None and request.expires_at <= now:
            await self._repository.update_approval_request(
                approval_request_id, {"status": ApprovalRequestStatus.EXPIRED.value}
            )
            raise GovernanceConflictError("Approval request has expired")
        if actor.user.user_id == request.requested_by:
            raise GovernanceConflictError("Requester cannot approve the same request")
        candidate = await self._training_repository.get_phase3_model_candidate(request.candidate_id)
        if (
            candidate is not None
            and decision_type == ApprovalDecisionType.MODEL
            and actor.user.user_id == candidate.creator
        ):
            raise GovernanceConflictError("Candidate creator cannot provide final model approval")
        if (
            decision_type == ApprovalDecisionType.SECURITY
            and RoleName.SECURITY_REVIEWER not in actor.roles
            and Permission.CANDIDATES_SECURITY_APPROVE not in actor.permissions
        ):
            raise GovernanceServiceError("Security approval requires a security reviewer role")
        if (
            decision_type == ApprovalDecisionType.MODEL
            and RoleName.MODEL_APPROVER not in actor.roles
            and Permission.CANDIDATES_STAGE_APPROVE not in actor.permissions
        ):
            raise GovernanceServiceError("Model approval requires a model approver role")
        existing_decisions = await self._repository.list_decisions(approval_request_id)
        if any(
            item.approved and item.reviewer_id == actor.user.user_id for item in existing_decisions
        ):
            raise GovernanceConflictError(
                "A reviewer cannot satisfy multiple approval requirements"
            )
        if any(
            item.decision_type == decision_type and item.reviewer_id == actor.user.user_id
            for item in existing_decisions
        ):
            raise GovernanceConflictError("Duplicate approval decision is not allowed")
        decision = ApprovalDecision(
            decision_id=stable_id(
                "appr_dec",
                f"{approval_request_id}:{actor.user.user_id}:{decision_type.value}:{now.isoformat()}",
            ),
            approval_request_id=approval_request_id,
            candidate_id=request.candidate_id,
            reviewer_id=actor.user.user_id,
            reviewer_roles=[role.value for role in actor.roles],
            decision_type=decision_type,
            approved=approved,
            notes=notes,
            created_at=now,
        )
        await self._repository.record_decision(decision)
        await self._record_audit(
            actor,
            f"governance.approval_request.{decision_type.value}",
            "approval_request",
            approval_request_id,
            "approved" if approved else "rejected",
            notes,
            "high" if not approved else "medium",
        )
        decisions = await self._repository.list_decisions(approval_request_id)
        if not approved:
            request = await self._repository.update_approval_request(
                approval_request_id, {"status": ApprovalRequestStatus.REJECTED.value}
            )
            return {"request": request, "decisions": decisions}
        approved_types = {item.decision_type for item in decisions if item.approved}
        reviewers = {item.reviewer_id for item in decisions if item.approved}
        if (
            all(item in approved_types for item in request.required_decisions)
            and len(reviewers) >= 2
        ):
            request = await self._repository.update_approval_request(
                approval_request_id, {"status": ApprovalRequestStatus.APPROVED.value}
            )
        return {"request": request, "decisions": decisions}

    async def cancel_approval_request(
        self, approval_request_id: str, reason: str, actor: AuthenticatedPrincipal
    ) -> ApprovalRequest:
        request = await self._repository.get_approval_request(approval_request_id)
        if request is None:
            raise GovernanceServiceError("Approval request not found")
        if request.status != ApprovalRequestStatus.PENDING:
            raise GovernanceConflictError("Only pending approval requests can be cancelled")
        cancelled = await self._repository.update_approval_request(
            approval_request_id, {"status": ApprovalRequestStatus.CANCELLED.value}
        )
        if cancelled is None:
            raise GovernanceServiceError("Approval request not found")
        await self._record_audit(
            actor,
            "governance.approval_request.cancel",
            "approval_request",
            approval_request_id,
            "success",
            reason,
            "medium",
        )
        return cancelled

    async def emergency_override(
        self, approval_request_id: str, reason: str, actor: AuthenticatedPrincipal
    ) -> ApprovalRequest:
        if Permission.EMERGENCY_REVOKE not in actor.permissions:
            raise GovernanceServiceError("Emergency override permission is required")
        if not reason.strip():
            raise GovernanceServiceError("Emergency override reason is required")
        request = await self._repository.get_approval_request(approval_request_id)
        if request is None:
            raise GovernanceServiceError("Approval request not found")
        if request.status not in {
            ApprovalRequestStatus.PENDING,
            ApprovalRequestStatus.REJECTED,
            ApprovalRequestStatus.EXPIRED,
        }:
            raise GovernanceConflictError("Approval request cannot be overridden in this state")
        updated = await self._repository.update_approval_request(
            approval_request_id, {"status": ApprovalRequestStatus.APPROVED.value}
        )
        if updated is None:
            raise GovernanceServiceError("Approval request not found")
        await self._repository.record_security_event(
            {
                "event_id": stable_id(
                    "secevt", f"emergency_override:{approval_request_id}:{utc_now().isoformat()}"
                ),
                "severity": "critical",
                "event_type": "emergency_governance_override",
                "actor_user_id": actor.user.user_id,
                "resource_type": "approval_request",
                "resource_id": approval_request_id,
                "reason": reason,
                "metadata": {"candidate_id": request.candidate_id},
                "created_at": utc_now(),
            }
        )
        await self._record_audit(
            actor,
            "governance.emergency_override",
            "approval_request",
            approval_request_id,
            "success",
            reason,
            "critical",
        )
        return updated

    async def create_staging_request(
        self,
        candidate_id: str,
        approval_request_id: str,
        staging_environment: str,
        reason: str,
        actor: AuthenticatedPrincipal,
    ) -> StagingRequest:
        if staging_environment != "manual_staging":
            raise GovernanceServiceError("Only manual_staging is supported in Phase 4")
        candidate = await self._training_repository.get_phase3_model_candidate(candidate_id)
        if candidate is None:
            raise GovernanceServiceError("Model candidate not found")
        if candidate.approval_state != ManifestReviewStatus.APPROVED:
            raise GovernanceServiceError("Candidate is not approved for manual staging")
        if (
            candidate.deployment_recommendation
            != DeploymentRecommendationStatus.RECOMMENDED_FOR_MANUAL_STAGING
        ):
            raise GovernanceServiceError("Candidate recommendation does not permit manual staging")
        if not candidate.adapter_hash or len(candidate.adapter_hash) < 32:
            raise GovernanceServiceError("Candidate adapter hash is missing or invalid")
        if not candidate.adapter_location:
            raise GovernanceServiceError("Candidate adapter location is missing")
        if candidate.safety_status != "passed":
            raise GovernanceServiceError("Candidate safety gate has not passed")
        if candidate.license_status != "approved":
            raise GovernanceServiceError("Candidate license gate has not passed")
        if candidate.regression_results.get("blocking"):
            raise GovernanceServiceError("Candidate has blocking regressions")
        if not candidate.rollback_information:
            raise GovernanceServiceError("Rollback metadata is required")
        approval = await self._repository.get_approval_request(approval_request_id)
        if (
            approval is None
            or approval.candidate_id != candidate_id
            or approval.status != ApprovalRequestStatus.APPROVED
        ):
            raise GovernanceServiceError("Approved governance request is required")
        if actor.user.user_id == approval.requested_by:
            raise GovernanceConflictError(
                "Approval requester cannot execute their own staging request"
            )
        now = utc_now()
        request = StagingRequest(
            staging_request_id=stable_id(
                "stage", f"{candidate_id}:{approval_request_id}:{now.isoformat()}"
            ),
            candidate_id=candidate_id,
            approval_request_id=approval_request_id,
            requested_by=actor.user.user_id,
            status=StagingRequestStatus.READY_FOR_MANUAL_STAGING,
            staging_environment=staging_environment,
            adapter_hash=candidate.adapter_hash,
            reason=reason,
            created_at=now,
            updated_at=now,
        )
        await self._repository.create_staging_request(request)
        await self._record_staging_event(
            request.staging_request_id,
            candidate_id,
            actor,
            "manual_staging_ready",
            "success",
            reason,
        )
        return request

    async def record_manual_assignment(
        self, staging_request_id: str, actor: AuthenticatedPrincipal
    ) -> ProductionModelAssignment:
        request = await self._repository.get_staging_request(staging_request_id)
        if request is None:
            raise GovernanceServiceError("Staging request not found")
        if request.status != StagingRequestStatus.READY_FOR_MANUAL_STAGING:
            raise GovernanceConflictError("Staging request is not ready")
        now = utc_now()
        assignment = ProductionModelAssignment(
            assignment_id=stable_id("assign", f"{staging_request_id}:{now.isoformat()}"),
            environment=request.staging_environment,
            candidate_id=request.candidate_id,
            adapter_hash=request.adapter_hash,
            assigned_by=actor.user.user_id,
            active=True,
            created_at=now,
        )
        await self._repository.record_assignment(assignment)
        await self._repository.update_staging_request(
            staging_request_id, {"status": StagingRequestStatus.ASSIGNMENT_RECORDED.value}
        )
        await self._record_staging_event(
            staging_request_id,
            request.candidate_id,
            actor,
            "manual_staging_assignment_recorded",
            "success",
            None,
        )
        return assignment

    async def rollback_staging_request(
        self, staging_request_id: str, reason: str, actor: AuthenticatedPrincipal
    ) -> StagingRequest:
        existing = await self._repository.get_staging_request(staging_request_id)
        if existing is None:
            raise GovernanceServiceError("Staging request not found")
        if existing.status not in {
            StagingRequestStatus.READY_FOR_MANUAL_STAGING,
            StagingRequestStatus.ASSIGNMENT_RECORDED,
        }:
            raise GovernanceConflictError("Staging request cannot be rolled back in this state")
        request = await self._repository.update_staging_request(
            staging_request_id, {"status": StagingRequestStatus.ROLLED_BACK.value}
        )
        if request is None:
            raise GovernanceServiceError("Staging request not found")
        await self._record_staging_event(
            staging_request_id,
            request.candidate_id,
            actor,
            "manual_staging_rollback",
            "success",
            reason,
        )
        return request

    async def _record_staging_event(
        self,
        staging_request_id: str,
        candidate_id: str,
        actor: AuthenticatedPrincipal,
        event_type: str,
        result: str,
        reason: str | None,
    ) -> None:
        now = utc_now()
        await self._repository.record_staging_event(
            StagingEvent(
                event_id=stable_id(
                    "stage_evt", f"{staging_request_id}:{event_type}:{now.isoformat()}"
                ),
                staging_request_id=staging_request_id,
                candidate_id=candidate_id,
                actor_user_id=actor.user.user_id,
                event_type=event_type,
                result=result,
                reason=reason,
                risk_level="high" if event_type.endswith("rollback") else "medium",
                created_at=now,
            )
        )
        await self._record_audit(
            actor,
            f"governance.{event_type}",
            "staging_request",
            staging_request_id,
            result,
            reason,
            "high" if event_type.endswith("rollback") else "medium",
        )

    async def _record_audit(
        self,
        actor: AuthenticatedPrincipal,
        action: str,
        resource_type: str,
        resource_id: str | None,
        result: str,
        reason: str | None,
        risk_level: str,
    ) -> None:
        now = utc_now()
        await self._repository.record_audit_event(
            {
                "event_id": stable_id("audit", f"{action}:{resource_id}:{now.isoformat()}"),
                "actor_user_id": actor.user.user_id,
                "actor_session_id": actor.session_id,
                "actor_roles": [role.value for role in actor.roles],
                "actor_permissions": [permission.value for permission in actor.permissions],
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "result": result,
                "reason": reason,
                "risk_level": risk_level,
                "created_at": now,
            }
        )
