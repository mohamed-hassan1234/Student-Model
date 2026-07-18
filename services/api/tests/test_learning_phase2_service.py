from pathlib import Path
from typing import Any

import anyio
import pytest

from devmind_api.config import Settings
from devmind_api.technology.learning_models import (
    DatasetApprovalStatus,
    DatasetType,
    LearningCycleStatus,
    ModelCandidate,
    ReviewQueueStatus,
    TrainingConfig,
)
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.learning_services import (
    EvaluationGate,
    LearningOrchestrator,
    LearningServiceError,
    SafeCodeRunner,
    StaticCodeAnalyzer,
)
from devmind_api.technology.models import PermissionStatus
from devmind_api.technology.repositories import TechnologyRepository
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


def _orchestrator(fake_database: Any, tmp_path: Path) -> LearningOrchestrator:
    return LearningOrchestrator(
        LearningRepository(fake_database),
        TechnologyRepository(fake_database),
        _settings(tmp_path),
    )


async def test_curriculum_hierarchy_coverage_and_gap_detection(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)

    report = await orchestrator.curriculum.ensure_default_curriculum()
    gaps = await orchestrator.gaps.detect()

    assert report.curriculum_id == "technology-student-v0.1"
    assert len(report.topic_scores) >= 40
    assert {topic.domain for topic in report.topic_scores} >= {
        "Web Fundamentals",
        "Frontend",
        "Backend",
        "Database",
        "Development Tools",
        "Software Engineering",
    }
    assert gaps
    assert "no_approved_sources" in gaps[0].signals


async def test_learning_cycle_question_generation_is_bounded(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    cycle = await orchestrator.cycles.create_planned_cycle(
        domain="Frontend",
        topic="React",
        objectives=["Explain React state"],
        human_owner="test-admin",
        maximum_examples=999,
    )

    started = await orchestrator.cycles.transition(cycle.cycle_id, LearningCycleStatus.COLLECTING)
    questions = await orchestrator.questions.generate_for_cycle(cycle.cycle_id)

    assert started.status == LearningCycleStatus.COLLECTING
    assert len(questions) == 18
    assert questions[0].duplicate_status == "unique"


async def test_candidate_verification_review_dataset_version_and_export(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    await fake_database["document_chunks"].insert_one(
        {
            "_id": "chunk-react-state",
            "technology_topic": "react",
            "chunk": {
                "text": "React state stores component data that can change over time.",
                "retrieval_use_status": "allowed",
                "license_status": "approved",
            },
        }
    )
    cycle = await orchestrator.cycles.create_planned_cycle(
        domain="Frontend",
        topic="React",
        objectives=["Explain state"],
        human_owner="test-admin",
        maximum_examples=1,
    )
    question = (await orchestrator.questions.generate_for_cycle(cycle.cycle_id))[0]
    evidence = await orchestrator.evidence.retrieve(question.topic)
    candidate = await orchestrator.candidates.generate(question, evidence)
    verification = await orchestrator.verifier.verify(candidate)
    review = await orchestrator.reviews.enqueue(candidate)
    approved = await orchestrator.reviews.act(
        review_id=review.review_id,
        reviewer_id="reviewer-1",
        action="approve",
        note="Supported by cited evidence.",
    )
    record = await orchestrator.datasets.build_from_review(approved.review_id, DatasetType.SFT)
    version = await orchestrator.versions.create_version(
        record.dataset_candidate_id,
        "Technology SFT v0.1",
        "Approved test dataset",
        "reviewer-1",
    )
    export = await orchestrator.exporter.export_version(version.dataset_version_id)
    stored_record = await orchestrator.repository.get_dataset_record(record.record_id)

    assert candidate.training_use_eligibility is True
    assert verification.requires_human_review is True
    assert verification.overall_score >= 0.7
    assert approved.status == ReviewQueueStatus.APPROVED
    assert record.human_approval_status == ReviewQueueStatus.APPROVED
    assert version.immutable is True
    assert stored_record is not None
    assert stored_record.dataset_version == version.dataset_version_id
    exported_text = await anyio.Path(export["data_path"]).read_text(encoding="utf-8")
    assert exported_text.count("\n") == 1
    assert await anyio.Path(export["license_manifest_path"]).exists()
    assert await anyio.Path(export["source_provenance_manifest_path"]).exists()
    assert await anyio.Path(export["verification_report_path"]).exists()


async def test_human_review_is_required_before_dataset_record(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)

    with pytest.raises(LearningServiceError):
        await orchestrator.datasets.build_from_review("missing-review", DatasetType.SFT)


async def test_dataset_versions_are_immutable(fake_database: Any, tmp_path: Path) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    version = await _sample_dataset_version(orchestrator, "immutable-test")

    with pytest.raises(ValueError):
        await LearningRepository(fake_database).create_dataset_version(version)


async def test_export_filters_license_and_evaluation_records(
    fake_database: Any, tmp_path: Path
) -> None:
    repository = LearningRepository(fake_database)
    now = utc_now()
    allowed = _dataset_record(
        "record-allowed",
        "candidate-filter",
        license_status="approved",
        training_permission="allowed",
        evaluation_status="excluded_from_evaluation",
        now=now,
    )
    blocked = _dataset_record(
        "record-blocked",
        "candidate-filter",
        license_status="unknown",
        training_permission="allowed",
        evaluation_status="excluded_from_evaluation",
        now=now,
    )
    evaluation = _dataset_record(
        "record-eval",
        "candidate-filter",
        license_status="approved",
        training_permission="allowed",
        evaluation_status="evaluation_record",
        now=now,
    )
    await repository.create_dataset_record(allowed)
    await repository.create_dataset_record(blocked)
    await repository.create_dataset_record(evaluation)
    version = await _orchestrator(fake_database, tmp_path).versions.create_version(
        "candidate-filter", "Filtered", "Filtered records", "reviewer"
    )

    assert version.approved_record_count == 1
    assert version.content_manifest_hash


async def test_frozen_evaluation_records_are_persisted(fake_database: Any, tmp_path: Path) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)

    evaluation_set = await orchestrator.evaluations.ensure_default_evaluation_set()
    records = await orchestrator.repository.list_evaluation_records()

    assert evaluation_set.frozen is True
    assert len(records) == len(evaluation_set.record_ids)


async def test_static_analyzer_and_disabled_safe_runner(fake_database: Any, tmp_path: Path) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    cycle = await orchestrator.cycles.create_planned_cycle(
        domain="Web Fundamentals",
        topic="JavaScript",
        objectives=["Detect unsafe code"],
        human_owner="test-admin",
        maximum_examples=1,
    )
    question = (await orchestrator.questions.generate_for_cycle(cycle.cycle_id))[0]
    candidate = await orchestrator.candidates.generate(question, [])
    unsafe = candidate.model_copy(update={"generated_answer": "Use eval(userInput)."})

    signal = StaticCodeAnalyzer().analyze(unsafe)
    runner_signal = SafeCodeRunner(_settings(tmp_path)).capability_signal(candidate.candidate_id)

    assert signal.passed is False
    assert runner_signal.details["status"] == "disabled_static_checks_only"


async def test_training_config_validation_and_candidate_gate(
    fake_database: Any, tmp_path: Path
) -> None:
    orchestrator = _orchestrator(fake_database, tmp_path)
    config = TrainingConfig(
        training_config_id="train-config-test",
        base_model_identifier="local-base",
        base_model_revision="rev1",
        base_model_license="review-required",
        tokenizer_identifier="local-tokenizer",
        tokenizer_revision="rev1",
        dataset_version="dataset-v1",
        evaluation_set_version="eval-v1",
        training_method="mock_dry_run",
        learning_rate=0.0001,
        epochs=1,
        sequence_length=512,
        seed=7,
        output_directory="storage/generated/training/out",
        logging_directory="storage/generated/training/logs",
    )
    candidate = ModelCandidate(
        candidate_id="model-candidate-test",
        base_model="local-base",
        base_model_revision="rev1",
        base_model_license="review-required",
        adapter_location="storage/generated/adapters/test",
        adapter_hash="abc123",
        training_config_version=config.training_config_id,
        dataset_version="dataset-v1",
        evaluation_set_version="eval-v1",
        evaluation_metrics={"citation_correctness": 0.7},
        safety_metrics={"prompt_injection_resistance": 0.9},
        created_at=utc_now(),
        creator="test-admin",
        approval_state=DatasetApprovalStatus.PENDING,
        rollback_metadata={"previous_model": "current-local"},
    )

    validation = orchestrator.training_configs.validate(config)
    recommendation = EvaluationGate().evaluate(candidate)

    assert validation["training_starts_automatically"] is False
    assert recommendation.recommended is False
    assert "human_approval_missing" in recommendation.reasons


async def _sample_dataset_version(orchestrator: LearningOrchestrator, seed: str) -> Any:
    now = utc_now()
    record = _dataset_record(
        f"record-{seed}",
        f"candidate-{seed}",
        license_status="approved",
        training_permission="allowed",
        evaluation_status="excluded_from_evaluation",
        now=now,
    )
    await orchestrator.repository.create_dataset_record(record)
    return await orchestrator.versions.create_version(
        record.dataset_candidate_id, "Immutable", "Immutable version", "reviewer"
    )


def _dataset_record(
    record_id: str,
    candidate_id: str,
    *,
    license_status: str,
    training_permission: str,
    evaluation_status: str,
    now: Any,
) -> Any:
    from devmind_api.technology.learning_models import DatasetRecord

    return DatasetRecord(
        record_id=record_id,
        dataset_candidate_id=candidate_id,
        dataset_type=DatasetType.SFT,
        creation_timestamp=now,
        domain="Frontend",
        topic="React",
        source_provenance=[{"source_context_id": "chunk-1"}],
        source_license_metadata=[{"license_status": license_status}],
        retrieval_use_permission=PermissionStatus.ALLOWED.value,
        training_use_permission=training_permission,
        teacher_provenance=[{"provider": "mock", "model": "mock-devmind-teacher"}],
        teacher_output_training_permission=training_permission,
        verification_scores={"overall": 0.9, "risk": 0.1},
        human_approval_status=ReviewQueueStatus.APPROVED,
        reviewer_id="reviewer",
        review_timestamp=now,
        content_hash=f"hash-{record_id}",
        evaluation_set_exclusion_status=evaluation_status,
        question="What is React state?",
        answer="React state stores component data that can change.",
    )
