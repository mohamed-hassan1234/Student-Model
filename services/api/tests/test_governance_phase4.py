from datetime import timedelta

import pytest
from fakes import FakeMongoDatabase

from devmind_api.auth.models import AuthenticatedPrincipal, CreateUserInput, RoleName
from devmind_api.auth.repositories import AuthRepository
from devmind_api.auth.services import AuthService
from devmind_api.config import Settings
from devmind_api.governance.models import ApprovalDecisionType
from devmind_api.governance.repositories import GovernanceRepository
from devmind_api.governance.services import (
    GovernanceConflictError,
    GovernanceService,
    GovernanceServiceError,
)
from devmind_api.technology.training_models import (
    DeploymentRecommendationStatus,
    ManifestReviewStatus,
    Phase3ModelCandidate,
)
from devmind_api.technology.training_repositories import TrainingRepository
from devmind_shared.time import utc_now

pytestmark = pytest.mark.anyio


async def test_governance_requires_distinct_reviewers_and_all_decisions(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    engineer = await _principal(auth, "engineer@example.com", "engineer", RoleName.AI_ENGINEER)
    model = await _principal(auth, "model@example.com", "model", RoleName.MODEL_APPROVER)
    security = await _principal(
        auth, "security@example.com", "security", RoleName.SECURITY_REVIEWER
    )
    operator = await _principal(auth, "operator@example.com", "operator", RoleName.OPERATOR)
    training_repo = TrainingRepository(fake_database)
    candidate = await training_repo.create_model_candidate(_approved_candidate())
    service = GovernanceService(GovernanceRepository(fake_database), training_repo)

    request = await service.create_approval_request(
        candidate.candidate_id, "Ready to review", engineer
    )
    await service.decide(
        request.approval_request_id, ApprovalDecisionType.MODEL, True, "Model approved", model
    )
    intermediate = await GovernanceRepository(fake_database).get_approval_request(
        request.approval_request_id
    )
    assert intermediate is not None
    assert intermediate.status == "pending"

    result = await service.decide(
        request.approval_request_id,
        ApprovalDecisionType.SECURITY,
        True,
        "Security approved",
        security,
    )
    assert result["request"].status == "approved"

    staging = await service.create_staging_request(
        candidate.candidate_id,
        request.approval_request_id,
        "manual_staging",
        "Operator records manual staging metadata",
        operator,
    )
    assignment = await service.record_manual_assignment(staging.staging_request_id, operator)
    assert assignment.environment == "manual_staging"
    assert assignment.candidate_id == candidate.candidate_id


async def test_requester_cannot_self_approve(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    requester = await _principal(auth, "model@example.com", "model", RoleName.MODEL_APPROVER)
    training_repo = TrainingRepository(fake_database)
    candidate = await training_repo.create_model_candidate(_approved_candidate())
    service = GovernanceService(GovernanceRepository(fake_database), training_repo)
    request = await service.create_approval_request(candidate.candidate_id, "Review me", requester)

    with pytest.raises(GovernanceServiceError, match="Requester cannot approve"):
        await service.decide(
            request.approval_request_id,
            ApprovalDecisionType.MODEL,
            True,
            "Self approval",
            requester,
        )


async def test_candidate_creator_cannot_final_approve(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    engineer = await _principal(auth, "engineer5@example.com", "engineer5", RoleName.AI_ENGINEER)
    model = await _principal(auth, "model5@example.com", "model5", RoleName.MODEL_APPROVER)
    training_repo = TrainingRepository(fake_database)
    candidate = _approved_candidate("candidate-creator").model_copy(
        update={"creator": model.user.user_id}
    )
    await training_repo.create_model_candidate(candidate)
    service = GovernanceService(GovernanceRepository(fake_database), training_repo)
    request = await service.create_approval_request(candidate.candidate_id, "Review me", engineer)

    with pytest.raises(GovernanceConflictError, match="creator"):
        await service.decide(
            request.approval_request_id,
            ApprovalDecisionType.MODEL,
            True,
            "Creator approval",
            model,
        )


async def test_duplicate_or_multi_type_approval_is_rejected(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    engineer = await _principal(auth, "engineer2@example.com", "engineer2", RoleName.AI_ENGINEER)
    reviewer = await _principal(auth, "multi@example.com", "multi", RoleName.SUPER_ADMIN)
    training_repo = TrainingRepository(fake_database)
    candidate = await training_repo.create_model_candidate(_approved_candidate())
    service = GovernanceService(GovernanceRepository(fake_database), training_repo)
    request = await service.create_approval_request(candidate.candidate_id, "Review me", engineer)

    await service.decide(
        request.approval_request_id, ApprovalDecisionType.MODEL, True, "Model approved", reviewer
    )
    with pytest.raises(GovernanceConflictError, match="multiple approval"):
        await service.decide(
            request.approval_request_id,
            ApprovalDecisionType.SECURITY,
            True,
            "Security approved",
            reviewer,
        )


async def test_expired_and_cancelled_approval_transitions_are_rejected(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    engineer = await _principal(auth, "engineer3@example.com", "engineer3", RoleName.AI_ENGINEER)
    model = await _principal(auth, "model3@example.com", "model3", RoleName.MODEL_APPROVER)
    training_repo = TrainingRepository(fake_database)
    candidate = await training_repo.create_model_candidate(_approved_candidate("candidate-expiry"))
    governance_repo = GovernanceRepository(fake_database)
    service = GovernanceService(governance_repo, training_repo)
    request = await service.create_approval_request(candidate.candidate_id, "Review me", engineer)

    await governance_repo.update_approval_request(
        request.approval_request_id, {"expires_at": utc_now() - timedelta(minutes=1)}
    )
    with pytest.raises(GovernanceConflictError, match="expired"):
        await service.decide(
            request.approval_request_id,
            ApprovalDecisionType.MODEL,
            True,
            "Too late",
            model,
        )

    request = await service.create_approval_request(candidate.candidate_id, "Cancel me", engineer)
    cancelled = await service.cancel_approval_request(
        request.approval_request_id, "No longer needed", engineer
    )
    assert cancelled.status == "cancelled"
    with pytest.raises(GovernanceConflictError, match="pending"):
        await service.decide(
            request.approval_request_id,
            ApprovalDecisionType.MODEL,
            True,
            "Cancelled",
            model,
        )


async def test_emergency_override_requires_permission_and_records_security_event(
    fake_database: FakeMongoDatabase, test_settings: Settings
) -> None:
    auth = AuthService(AuthRepository(fake_database), test_settings)
    engineer = await _principal(auth, "engineer4@example.com", "engineer4", RoleName.AI_ENGINEER)
    admin = await _principal(auth, "superadmin@example.com", "superadmin", RoleName.SUPER_ADMIN)
    training_repo = TrainingRepository(fake_database)
    candidate = await training_repo.create_model_candidate(
        _approved_candidate("candidate-override")
    )
    service = GovernanceService(GovernanceRepository(fake_database), training_repo)
    request = await service.create_approval_request(candidate.candidate_id, "Override me", engineer)

    overridden = await service.emergency_override(
        request.approval_request_id, "Emergency local security review override", admin
    )

    assert overridden.status == "approved"
    security_events = fake_database["security_events"].documents
    assert any(event["event_type"] == "emergency_governance_override" for event in security_events)


async def _principal(
    auth: AuthService, email: str, username: str, role: RoleName
) -> AuthenticatedPrincipal:
    user = await auth.create_user(
        CreateUserInput(
            email=email,
            username=username,
            display_name=username,
            roles=[role],
            **{"password": "StrongPassword123!"},  # noqa: S106 - deterministic test credential.
        ),
        actor=None,
    )
    tokens = await auth.login(str(user.email), "StrongPassword123!")
    return await auth.authenticate_access_token(str(tokens["access_token"]))


def _approved_candidate(candidate_id: str = "candidate-phase4") -> Phase3ModelCandidate:
    now = utc_now()
    return Phase3ModelCandidate(
        candidate_id=candidate_id,
        candidate_name="Technology Student Candidate",
        base_model_manifest_id="manifest",
        base_model_revision="abcdef123456",
        adapter_location="storage/generated/training/candidate",
        adapter_hash="a" * 64,
        training_run_id="run",
        training_config_version="config",
        dataset_version="dataset",
        evaluation_set_version="eval",
        baseline_results={"overall": 0.5},
        candidate_results={"overall": 0.7},
        regression_results={"blocking": []},
        safety_status="passed",
        license_status="approved",
        created_at=now,
        creator="engineer",
        approval_state=ManifestReviewStatus.APPROVED,
        deployment_recommendation=DeploymentRecommendationStatus.RECOMMENDED_FOR_MANUAL_STAGING,
        rollback_information={"previous_candidate": None},
    )
