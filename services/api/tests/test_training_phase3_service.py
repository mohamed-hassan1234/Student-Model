from pathlib import Path
from typing import Any

import pytest

from devmind_api.config import Settings
from devmind_api.technology.learning_models import (
    DatasetApprovalStatus,
    DatasetRecord,
    DatasetType,
    DatasetVersion,
    ReviewQueueStatus,
)
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.models import PermissionStatus
from devmind_api.technology.training_models import (
    BaseModelManifest,
    ManifestReviewStatus,
    ModelApprovalAction,
    Phase3TrainingConfig,
)
from devmind_api.technology.training_repositories import TrainingRepository
from devmind_api.technology.training_services import (
    Phase3TrainingOrchestrator,
    RegressionDetector,
)
from devmind_shared.time import utc_now

pytestmark = pytest.mark.anyio


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        APP_ENV="test",
        MONGODB_URI="mongodb://example.invalid:27017",
        MONGODB_DATABASE="devmind_test",
        MONGODB_TEST_DATABASE="devmind_test",
        STORAGE_DIRECTORY=tmp_path,
    )


def _orchestrator(fake_database: Any, tmp_path: Path) -> Phase3TrainingOrchestrator:
    return Phase3TrainingOrchestrator(
        TrainingRepository(fake_database),
        LearningRepository(fake_database),
        _settings(tmp_path),
    )


async def test_base_model_manifest_validation_gates_license_revision_and_remote_code(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    manifest = _manifest(approval=ManifestReviewStatus.PENDING, remote_code=True)

    validation = orchestrator.base_models.validate_manifest(manifest)
    stored = await orchestrator.base_models.register(manifest)
    approved = await orchestrator.base_models.approve_or_reject(
        stored.manifest_id, ManifestReviewStatus.APPROVED
    )

    assert validation["valid"] is False
    assert "manifest_not_approved" in validation["blocking_issues"]
    assert "remote_code_not_approved" in validation["blocking_issues"]
    assert approved.approval_status == ManifestReviewStatus.APPROVED


async def test_dataset_gate_and_split_reproducibility(fake_database: Any, tmp_path: Path) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    await _seed_dataset(fake_database, "dsv-phase3", count=5)

    report = await orchestrator.dataset_gate.validate("dsv-phase3")
    split_a = await orchestrator.splits.create_split("dsv-phase3", seed=11)
    split_b = await orchestrator.splits.create_split("dsv-phase3", seed=11)

    assert report.valid is True
    assert report.approved_record_count == 5
    assert split_a.manifest_hash == split_b.manifest_hash
    group_splits: dict[str, set[str]] = {}
    for item in split_a.items:
        group_splits.setdefault(item.group_id, set()).add(item.split)
    assert all(len(splits) == 1 for splits in group_splits.values())


async def test_training_config_smoke_training_artifacts_and_resume(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    await orchestrator.base_models.register(_manifest(approval=ManifestReviewStatus.APPROVED))
    await _seed_dataset(fake_database, "dsv-smoke", count=3)
    split = await orchestrator.splits.create_split("dsv-smoke", seed=7)
    config = _training_config(tmp_path, split.split_manifest_id, "dsv-smoke")

    validation = await orchestrator.configs.validate_and_save(config)
    run = await orchestrator.runs.create_run(config.training_config_id, "trainer")
    completed = await orchestrator.runs.run_smoke_training(run.run_id)
    resume = await orchestrator.runs.resume_validation(
        completed.run_id, completed.checkpoints[0].path
    )
    artifacts = await orchestrator.training_repository.list_training_artifacts(completed.run_id)

    assert validation["valid"] is True
    assert validation["training_starts_automatically"] is False
    assert completed.status.value == "completed"
    assert completed.adapter_hash is not None
    assert len(artifacts) == 4
    assert resume["resumable"] is True


async def test_candidate_evaluation_regression_recommendation_and_approval(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    await orchestrator.base_models.register(_manifest(approval=ManifestReviewStatus.APPROVED))
    await _seed_dataset(fake_database, "dsv-candidate", count=3)
    split = await orchestrator.splits.create_split("dsv-candidate", seed=7)
    config = _training_config(tmp_path, split.split_manifest_id, "dsv-candidate")
    await orchestrator.configs.validate_and_save(config)
    run = await orchestrator.runs.create_run(config.training_config_id, "trainer")
    completed = await orchestrator.runs.run_smoke_training(run.run_id)
    baseline = await orchestrator.evaluations.record_baseline_unavailable(
        "base-model", "eval-v1", "No approved inference host configured."
    )
    candidate_eval = await orchestrator.evaluations.record_candidate_mock_evaluation(
        "candidate-subject", "eval-v1"
    )
    candidate = await orchestrator.candidates.register(
        candidate_name="Technology Student v0.1 Candidate",
        training_run_id=completed.run_id,
        baseline_evaluation_id=baseline.evaluation_id,
        candidate_evaluation_id=candidate_eval.evaluation_id,
        creator="trainer",
    )
    recommendation = await orchestrator.recommendations.generate_for_candidate(
        orchestrator.training_repository, candidate.candidate_id
    )
    approval = await orchestrator.approvals.act(
        candidate_id=candidate.candidate_id,
        reviewer_id="reviewer",
        action=ModelApprovalAction.REQUEST_MORE_EVALUATION,
        notes="Smoke candidate only.",
    )
    adapter_check = await orchestrator.adapter_loader.check(candidate.candidate_id)

    assert candidate.approval_state == ManifestReviewStatus.PENDING
    assert recommendation.recommendation.value == "needs_more_evaluation"
    assert approval.action == ModelApprovalAction.REQUEST_MORE_EVALUATION
    assert adapter_check.loadable is False
    assert "candidate_not_approved_for_manual_staging" in adapter_check.reasons


def test_regression_detector_blocks_safety_regression() -> None:
    result = RegressionDetector().detect(
        {"citation_correctness": 0.9, "react": 0.8},
        {"citation_correctness": 0.7, "react": 0.82},
    )

    assert "citation_correctness_regressed" in result["blocking_regressions"]


async def _seed_dataset(fake_database: Any, dataset_version_id: str, count: int) -> None:
    repository = LearningRepository(fake_database)
    now = utc_now()
    for index in range(count):
        await repository.create_dataset_record(
            DatasetRecord(
                record_id=f"record-{dataset_version_id}-{index}",
                dataset_candidate_id=f"candidate-{dataset_version_id}",
                dataset_version=dataset_version_id,
                dataset_type=DatasetType.SFT,
                creation_timestamp=now,
                domain="Frontend",
                topic="React",
                source_provenance=[{"source_context_id": f"chunk-{index}"}],
                source_license_metadata=[{"license_status": "approved"}],
                retrieval_use_permission=PermissionStatus.ALLOWED.value,
                training_use_permission=PermissionStatus.ALLOWED.value,
                teacher_provenance=[{"provider": "mock", "model": "mock-teacher"}],
                teacher_output_training_permission=PermissionStatus.ALLOWED.value,
                verification_scores={"overall": 0.9, "risk": 0.1},
                human_approval_status=ReviewQueueStatus.APPROVED,
                reviewer_id="reviewer",
                review_timestamp=now,
                content_hash=f"content-hash-{dataset_version_id}-{index}",
                leakage_check="passed",
                evaluation_set_exclusion_status="excluded_from_evaluation",
                question=f"What is React state {index}?",
                answer="React state stores component data that changes over time.",
            )
        )
    await repository.create_dataset_version(
        DatasetVersion(
            dataset_version_id=dataset_version_id,
            name="Phase 3 test dataset",
            description="Approved immutable test dataset",
            dataset_type=DatasetType.SFT,
            creation_timestamp=now,
            creator="reviewer",
            approved_record_count=count,
            rejected_record_count=0,
            domain_distribution={"Frontend": count},
            topic_distribution={"React": count},
            difficulty_distribution={"unspecified": count},
            source_distribution={},
            teacher_distribution={"mock": count},
            license_summary={"approved": count},
            verification_summary={"average_overall": 0.9, "average_risk": 0.1},
            content_manifest_hash=f"manifest-{dataset_version_id}",
            evaluation_exclusion_checks="passed",
            approval_status=DatasetApprovalStatus.APPROVED,
            approver="reviewer",
            approval_timestamp=now,
        )
    )


def _manifest(
    *,
    approval: ManifestReviewStatus,
    remote_code: bool = False,
) -> BaseModelManifest:
    now = utc_now()
    return BaseModelManifest(
        manifest_id="base-manifest-test",
        model_identifier="local/open-weight-test",
        exact_revision="0123456789abcdef",
        model_family="test-family",
        parameter_count="tiny",
        architecture="causal_lm",
        tokenizer_identifier="local/open-weight-test",
        tokenizer_revision="0123456789abcdef",
        context_length=2048,
        license_name="Apache-2.0",
        license_reference="LICENSE",
        commercial_use_status="allowed",
        fine_tuning_permission="allowed",
        redistribution_status="review_required",
        required_trust_remote_code=remote_code,
        trust_remote_code_approved=False,
        expected_memory_gb=1.0,
        expected_disk_gb=1.0,
        minimum_recommended_hardware={"ram_gb": 8},
        human_license_review_status=approval,
        approval_status=approval,
        created_by="local-admin",
        created_at=now,
        updated_at=now,
    )


def _training_config(
    tmp_path: Path, split_manifest_id: str, dataset_version_id: str
) -> Phase3TrainingConfig:
    return Phase3TrainingConfig(
        training_config_id=f"config-{split_manifest_id}",
        experiment_name="phase3-smoke",
        base_model_manifest_id="base-manifest-test",
        dataset_version_id=dataset_version_id,
        split_manifest_id=split_manifest_id,
        evaluation_set_version="eval-v1",
        training_method="mock_smoke",
        output_directory=str(tmp_path / "generated" / split_manifest_id),
        created_at=utc_now(),
    )
