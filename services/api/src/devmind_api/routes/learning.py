from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from starlette import status

from devmind_api.auth.dependencies import require_permission
from devmind_api.auth.models import Permission
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoDatabase, get_database
from devmind_api.exceptions import DevMindError
from devmind_api.technology.learning_models import (
    DatasetType,
    LearningCycleStatus,
    ModelCandidate,
    ReviewQueueStatus,
    TrainingConfig,
)
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.learning_services import LearningOrchestrator, LearningServiceError
from devmind_api.technology.repositories import TechnologyRepository

router = APIRouter(prefix="/technology/learning", tags=["technology-learning"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


class CreateLearningCycleRequest(BaseModel):
    domain: str = Field(min_length=2, max_length=120)
    topic: str = Field(min_length=2, max_length=120)
    objectives: list[str] = Field(min_length=1, max_length=20)
    maximum_examples: int = Field(default=5, ge=1, le=500)
    human_owner: str = Field(default="authenticated-user", min_length=2, max_length=120)


class ReviewActionRequest(BaseModel):
    reviewer_id: str = Field(default="authenticated-user", min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=2000)
    edited_answer: str | None = Field(default=None, max_length=20000)
    rejection_reason: str | None = Field(default=None, max_length=2000)


class CreateDatasetVersionRequest(BaseModel):
    dataset_candidate_id: str
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=1000)
    creator: str = Field(default="authenticated-user", min_length=2, max_length=120)


class BuildDatasetRecordRequest(BaseModel):
    review_id: str
    dataset_type: DatasetType = DatasetType.SFT


def get_orchestrator(database: DatabaseDep, settings: SettingsDep) -> LearningOrchestrator:
    return LearningOrchestrator(
        LearningRepository(database), TechnologyRepository(database), settings
    )


OrchestratorDep = Annotated[LearningOrchestrator, Depends(get_orchestrator)]
TrainingConfigureDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_CONFIGURE))]
TrainingStartDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_START))]
TrainingCancelDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_CANCEL))]
DatasetReviewDep = Annotated[Any, Depends(require_permission(Permission.DATASETS_REVIEW))]
DatasetApproveDep = Annotated[Any, Depends(require_permission(Permission.DATASETS_APPROVE))]
DatasetExportDep = Annotated[Any, Depends(require_permission(Permission.DATASETS_EXPORT))]
CandidateCreateDep = Annotated[Any, Depends(require_permission(Permission.CANDIDATES_CREATE))]


@router.get("/curriculum")
async def read_curriculum(orchestrator: OrchestratorDep) -> Any:
    return await orchestrator.curriculum.ensure_default_curriculum()


@router.get("/curriculum/topics/{topic_id}")
async def read_topic(topic_id: str, database: DatabaseDep) -> Any:
    topic = await LearningRepository(database).get_curriculum_topic(topic_id)
    if topic is None:
        raise DevMindError("Curriculum topic not found", status.HTTP_404_NOT_FOUND)
    return topic


@router.get("/curriculum/coverage")
async def read_coverage(orchestrator: OrchestratorDep) -> Any:
    return await orchestrator.coverage.refresh()


@router.get("/curriculum/gaps")
async def read_knowledge_gaps(orchestrator: OrchestratorDep) -> Any:
    return {"gaps": await orchestrator.gaps.detect()}


@router.get("/curriculum/next-action")
async def recommend_next_learning_action(orchestrator: OrchestratorDep) -> Any:
    gaps = await orchestrator.gaps.detect()
    if not gaps:
        return {"action": "maintain_reviewed_dataset", "gap": None}
    gap = sorted(gaps, key=lambda item: item.severity, reverse=True)[0]
    return {"action": gap.recommended_action, "gap": gap}


@router.post("/cycles", status_code=status.HTTP_201_CREATED)
async def create_learning_cycle(
    request: CreateLearningCycleRequest,
    orchestrator: OrchestratorDep,
    principal: TrainingConfigureDep,
) -> Any:
    return await orchestrator.cycles.create_planned_cycle(
        domain=request.domain,
        topic=request.topic,
        objectives=request.objectives,
        human_owner=principal.user.user_id,
        maximum_examples=request.maximum_examples,
    )


@router.get("/cycles")
async def list_learning_cycles(database: DatabaseDep, limit: int = 50, offset: int = 0) -> Any:
    return {"cycles": await LearningRepository(database).list_learning_cycles(limit, offset)}


@router.get("/cycles/{cycle_id}")
async def read_learning_cycle(cycle_id: str, database: DatabaseDep) -> Any:
    cycle = await LearningRepository(database).get_learning_cycle(cycle_id)
    if cycle is None:
        raise DevMindError("Learning cycle not found", status.HTTP_404_NOT_FOUND)
    return cycle


@router.post("/cycles/{cycle_id}/start")
async def start_learning_cycle(
    cycle_id: str, orchestrator: OrchestratorDep, _: TrainingStartDep
) -> Any:
    try:
        return await orchestrator.cycles.transition(cycle_id, LearningCycleStatus.COLLECTING)
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/cycles/{cycle_id}/pause")
async def pause_learning_cycle(cycle_id: str, database: DatabaseDep, _: TrainingCancelDep) -> Any:
    updated = await LearningRepository(database).update_learning_cycle(
        cycle_id, {"status": LearningCycleStatus.PLANNED.value}
    )
    if updated is None:
        raise DevMindError("Learning cycle not found", status.HTTP_404_NOT_FOUND)
    return updated


@router.post("/cycles/{cycle_id}/cancel")
async def cancel_learning_cycle(
    cycle_id: str, orchestrator: OrchestratorDep, _: TrainingCancelDep
) -> Any:
    try:
        return await orchestrator.cycles.transition(cycle_id, LearningCycleStatus.CANCELLED)
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/cycles/{cycle_id}/metrics")
async def read_cycle_metrics(cycle_id: str, database: DatabaseDep) -> Any:
    cycle = await LearningRepository(database).get_learning_cycle(cycle_id)
    if cycle is None:
        raise DevMindError("Learning cycle not found", status.HTTP_404_NOT_FOUND)
    return {"cycle_id": cycle_id, "status": cycle.status, "metrics": cycle.metrics}


@router.post("/cycles/{cycle_id}/questions")
async def generate_cycle_questions(
    cycle_id: str, orchestrator: OrchestratorDep, _: TrainingStartDep
) -> Any:
    try:
        return {"questions": await orchestrator.questions.generate_for_cycle(cycle_id)}
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/questions")
async def list_generated_questions(database: DatabaseDep, limit: int = 50, offset: int = 0) -> Any:
    return {"questions": await LearningRepository(database).list_questions(limit, offset)}


@router.get("/questions/{question_id}")
async def read_generated_question(question_id: str, database: DatabaseDep) -> Any:
    question = await LearningRepository(database).get_question(question_id)
    if question is None:
        raise DevMindError("Generated question not found", status.HTTP_404_NOT_FOUND)
    return question


@router.post("/questions/{question_id}/candidate")
async def create_candidate_answer(
    question_id: str, orchestrator: OrchestratorDep, _: CandidateCreateDep
) -> Any:
    try:
        question = await orchestrator.repository.get_question(question_id)
        if question is None:
            raise LearningServiceError("Generated question not found")
        evidence = await orchestrator.evidence.retrieve(question.topic)
        candidate = await orchestrator.candidates.generate(question, evidence)
        verification = await orchestrator.verifier.verify(candidate)
        review = await orchestrator.reviews.enqueue(candidate)
        return {"candidate": candidate, "verification": verification, "review": review}
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/candidate-answers")
async def list_candidate_answers(database: DatabaseDep, limit: int = 50, offset: int = 0) -> Any:
    return {
        "candidate_answers": await LearningRepository(database).list_candidate_answers(
            limit, offset
        )
    }


@router.get("/candidate-answers/{candidate_id}")
async def read_candidate_answer(candidate_id: str, database: DatabaseDep) -> Any:
    candidate = await LearningRepository(database).get_candidate_answer(candidate_id)
    if candidate is None:
        raise DevMindError("Candidate answer not found", status.HTTP_404_NOT_FOUND)
    return candidate


@router.get("/candidate-answers/{candidate_id}/verification")
async def read_verification_report(candidate_id: str, database: DatabaseDep) -> Any:
    verification = await LearningRepository(database).get_latest_verification_run(candidate_id)
    if verification is None:
        raise DevMindError("Verification report not found", status.HTTP_404_NOT_FOUND)
    return verification


@router.get("/reviews")
async def list_pending_reviews(
    database: DatabaseDep,
    status_filter: Annotated[str | None, Query(alias="status")] = ReviewQueueStatus.PENDING.value,
    limit: int = 50,
    offset: int = 0,
) -> Any:
    return {
        "reviews": await LearningRepository(database).list_review_items(
            status=status_filter, limit=limit, offset=offset
        )
    }


@router.get("/reviews/{review_id}")
async def read_review_item(review_id: str, database: DatabaseDep) -> Any:
    review = await LearningRepository(database).get_review_item(review_id)
    if review is None:
        raise DevMindError("Review item not found", status.HTTP_404_NOT_FOUND)
    return review


@router.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    request: ReviewActionRequest,
    orchestrator: OrchestratorDep,
    principal: DatasetApproveDep,
) -> Any:
    try:
        return await orchestrator.reviews.act(
            review_id=review_id,
            reviewer_id=principal.user.user_id,
            action="approve",
            note=request.note,
        )
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/reviews/{review_id}/reject")
async def reject_review(
    review_id: str,
    request: ReviewActionRequest,
    orchestrator: OrchestratorDep,
    principal: DatasetReviewDep,
) -> Any:
    try:
        return await orchestrator.reviews.act(
            review_id=review_id,
            reviewer_id=principal.user.user_id,
            action="reject",
            rejection_reason=request.rejection_reason or request.note,
        )
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/reviews/{review_id}/edit-and-approve")
async def edit_and_approve_review(
    review_id: str,
    request: ReviewActionRequest,
    orchestrator: OrchestratorDep,
    principal: DatasetApproveDep,
) -> Any:
    try:
        return await orchestrator.reviews.act(
            review_id=review_id,
            reviewer_id=principal.user.user_id,
            action="edit_and_approve",
            note=request.note,
            edited_answer=request.edited_answer,
        )
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/reviews/{review_id}/request-regeneration")
async def request_regeneration(
    review_id: str,
    request: ReviewActionRequest,
    orchestrator: OrchestratorDep,
    principal: DatasetReviewDep,
) -> Any:
    try:
        return await orchestrator.reviews.act(
            review_id=review_id,
            reviewer_id=principal.user.user_id,
            action="request_regeneration",
            note=request.note,
        )
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/reviews/{review_id}/audit")
async def read_review_audit_history(review_id: str, database: DatabaseDep) -> Any:
    return {"actions": await LearningRepository(database).list_reviewer_actions(review_id)}


@router.get("/dataset-candidates")
async def list_dataset_candidates(database: DatabaseDep) -> Any:
    return {"dataset_candidates": await LearningRepository(database).list_dataset_candidates()}


@router.get("/dataset-candidates/{dataset_candidate_id}")
async def read_dataset_candidate(dataset_candidate_id: str, database: DatabaseDep) -> Any:
    candidate = await LearningRepository(database).get_dataset_candidate(dataset_candidate_id)
    if candidate is None:
        raise DevMindError("Dataset candidate not found", status.HTTP_404_NOT_FOUND)
    return candidate


@router.post("/dataset-records", status_code=status.HTTP_201_CREATED)
async def build_dataset_record(
    request: BuildDatasetRecordRequest, orchestrator: OrchestratorDep, _: DatasetApproveDep
) -> Any:
    try:
        return await orchestrator.datasets.build_from_review(
            request.review_id, request.dataset_type
        )
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/dataset-versions", status_code=status.HTTP_201_CREATED)
async def create_dataset_version(
    request: CreateDatasetVersionRequest,
    orchestrator: OrchestratorDep,
    principal: DatasetApproveDep,
) -> Any:
    try:
        return await orchestrator.versions.create_version(
            request.dataset_candidate_id, request.name, request.description, principal.user.user_id
        )
    except (LearningServiceError, ValueError) as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/dataset-versions")
async def list_dataset_versions(database: DatabaseDep) -> Any:
    return {"dataset_versions": await LearningRepository(database).list_dataset_versions()}


@router.get("/dataset-versions/{dataset_version_id}")
async def read_dataset_version(dataset_version_id: str, database: DatabaseDep) -> Any:
    version = await LearningRepository(database).get_dataset_version(dataset_version_id)
    if version is None:
        raise DevMindError("Dataset version not found", status.HTTP_404_NOT_FOUND)
    return version


@router.post("/dataset-versions/{dataset_version_id}/export")
async def export_dataset_version(
    dataset_version_id: str, orchestrator: OrchestratorDep, _: DatasetExportDep
) -> Any:
    try:
        return await orchestrator.exporter.export_version(dataset_version_id)
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/dataset-versions/{dataset_version_id}/export-status")
async def read_export_status(dataset_version_id: str, database: DatabaseDep) -> Any:
    version = await LearningRepository(database).get_dataset_version(dataset_version_id)
    if version is None:
        raise DevMindError("Dataset version not found", status.HTTP_404_NOT_FOUND)
    return {"dataset_version_id": dataset_version_id, "status": "export_on_request"}


@router.get("/evaluation-sets")
async def list_evaluation_sets(orchestrator: OrchestratorDep) -> Any:
    await orchestrator.evaluations.ensure_default_evaluation_set()
    return {"evaluation_sets": await orchestrator.repository.list_evaluation_sets()}


@router.get("/evaluation-sets/{evaluation_set_id}/summary")
async def read_evaluation_summary(evaluation_set_id: str, orchestrator: OrchestratorDep) -> Any:
    await orchestrator.evaluations.ensure_default_evaluation_set()
    sets = await orchestrator.repository.list_evaluation_sets()
    found = [item for item in sets if item.evaluation_set_id == evaluation_set_id]
    if not found:
        raise DevMindError("Evaluation set not found", status.HTTP_404_NOT_FOUND)
    evaluation_set = found[0]
    return {
        "evaluation_set_id": evaluation_set_id,
        "frozen": evaluation_set.frozen,
        "categories": evaluation_set.categories,
        "record_count": len(evaluation_set.record_ids),
        "training_export_exclusion": "enforced",
    }


@router.post("/training-configs/validate")
async def validate_training_config(request: TrainingConfig, orchestrator: OrchestratorDep) -> Any:
    return orchestrator.training_configs.validate(request)


@router.post("/model-candidates", status_code=status.HTTP_201_CREATED)
async def register_model_candidate(
    request: ModelCandidate, orchestrator: OrchestratorDep, _: CandidateCreateDep
) -> Any:
    try:
        candidate = await orchestrator.model_candidates.register(request)
        recommendation = orchestrator.gate.evaluate(candidate)
        await orchestrator.repository.record_deployment_recommendation(recommendation)
        return {"model_candidate": candidate, "deployment_recommendation": recommendation}
    except LearningServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/model-candidates")
async def list_model_candidates(database: DatabaseDep) -> Any:
    return {"model_candidates": await LearningRepository(database).list_model_candidates()}


@router.get("/model-candidates/{candidate_id}")
async def read_model_candidate(candidate_id: str, database: DatabaseDep) -> Any:
    candidate = await LearningRepository(database).get_model_candidate(candidate_id)
    if candidate is None:
        raise DevMindError("Model candidate not found", status.HTTP_404_NOT_FOUND)
    return candidate


@router.get("/model-candidates/{candidate_id}/deployment-recommendation")
async def read_deployment_recommendation(candidate_id: str, database: DatabaseDep) -> Any:
    recommendation = await LearningRepository(database).get_deployment_recommendation(candidate_id)
    if recommendation is None:
        raise DevMindError("Deployment recommendation not found", status.HTTP_404_NOT_FOUND)
    return recommendation
