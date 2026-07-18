from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette import status

from devmind_api.auth.dependencies import require_permission
from devmind_api.auth.models import Permission
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoDatabase, get_database
from devmind_api.exceptions import DevMindError
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.training_models import (
    BaseModelManifest,
    ManifestReviewStatus,
    ModelApprovalAction,
    Phase3TrainingConfig,
)
from devmind_api.technology.training_repositories import TrainingRepository
from devmind_api.technology.training_services import (
    Phase3TrainingOrchestrator,
    TrainingServiceError,
)

router = APIRouter(prefix="/technology/training", tags=["technology-training"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


class DatasetSplitRequest(BaseModel):
    seed: int = Field(default=7, ge=0)


class CreateTrainingRunRequest(BaseModel):
    training_config_id: str
    creator: str = Field(default="authenticated-user", min_length=2, max_length=120)


class BaselineUnavailableRequest(BaseModel):
    subject_id: str
    evaluation_set_version: str
    reason: str = Field(min_length=5, max_length=1000)


class CandidateEvaluationRequest(BaseModel):
    candidate_id: str
    evaluation_set_version: str
    scores: dict[str, float] | None = None


class RegisterCandidateRequest(BaseModel):
    candidate_name: str
    training_run_id: str
    baseline_evaluation_id: str
    candidate_evaluation_id: str
    creator: str = Field(default="authenticated-user", min_length=2, max_length=120)


class CompareCandidateRequest(BaseModel):
    baseline_evaluation_id: str
    candidate_evaluation_id: str


class ApprovalRequest(BaseModel):
    reviewer_id: str = Field(default="authenticated-user", min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


def get_training_orchestrator(
    database: DatabaseDep, settings: SettingsDep
) -> Phase3TrainingOrchestrator:
    return Phase3TrainingOrchestrator(
        TrainingRepository(database), LearningRepository(database), settings
    )


TrainingDep = Annotated[Phase3TrainingOrchestrator, Depends(get_training_orchestrator)]
TrainingConfigureDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_CONFIGURE))]
TrainingStartDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_START))]
TrainingCancelDep = Annotated[Any, Depends(require_permission(Permission.TRAINING_CANCEL))]
EvaluationStartDep = Annotated[Any, Depends(require_permission(Permission.EVALUATIONS_START))]
CandidateCreateDep = Annotated[Any, Depends(require_permission(Permission.CANDIDATES_CREATE))]
CandidateReviewDep = Annotated[Any, Depends(require_permission(Permission.CANDIDATES_REVIEW))]
CandidateStageDep = Annotated[Any, Depends(require_permission(Permission.CANDIDATES_STAGE_APPROVE))]


@router.post("/hardware/inspect")
async def inspect_hardware(orchestrator: TrainingDep, _: TrainingConfigureDep) -> Any:
    return await orchestrator.hardware.inspect()


@router.get("/hardware")
async def read_hardware_report(orchestrator: TrainingDep) -> Any:
    report = await orchestrator.hardware.latest()
    if report is None:
        return {"status": "not_inspected", "report": None}
    return {"status": "available", "report": report}


@router.post("/base-models", status_code=status.HTTP_201_CREATED)
async def register_base_model_manifest(
    request: BaseModelManifest, orchestrator: TrainingDep, _: TrainingConfigureDep
) -> Any:
    return await orchestrator.base_models.register(request)


@router.post("/base-models/validate")
async def validate_base_model_manifest(
    request: BaseModelManifest, orchestrator: TrainingDep
) -> Any:
    return orchestrator.base_models.validate_manifest(request)


@router.get("/base-models")
async def list_base_model_manifests(database: DatabaseDep) -> Any:
    return {"base_model_manifests": await TrainingRepository(database).list_base_model_manifests()}


@router.get("/base-models/{manifest_id}")
async def read_base_model_manifest(manifest_id: str, database: DatabaseDep) -> Any:
    manifest = await TrainingRepository(database).get_base_model_manifest(manifest_id)
    if manifest is None:
        raise DevMindError("Base-model manifest not found", status.HTTP_404_NOT_FOUND)
    return manifest


@router.post("/base-models/{manifest_id}/approve")
async def approve_base_model_manifest(
    manifest_id: str, orchestrator: TrainingDep, _: TrainingConfigureDep
) -> Any:
    try:
        return await orchestrator.base_models.approve_or_reject(
            manifest_id, ManifestReviewStatus.APPROVED
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/base-models/{manifest_id}/reject")
async def reject_base_model_manifest(
    manifest_id: str, orchestrator: TrainingDep, _: TrainingConfigureDep
) -> Any:
    try:
        return await orchestrator.base_models.approve_or_reject(
            manifest_id, ManifestReviewStatus.REJECTED
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/datasets/{dataset_version_id}/validate")
async def validate_dataset_version(
    dataset_version_id: str, orchestrator: TrainingDep, _: TrainingConfigureDep
) -> Any:
    return await orchestrator.dataset_gate.validate(dataset_version_id)


@router.post("/datasets/{dataset_version_id}/splits")
async def generate_split_manifest(
    dataset_version_id: str,
    request: DatasetSplitRequest,
    orchestrator: TrainingDep,
    _: TrainingConfigureDep,
) -> Any:
    try:
        return await orchestrator.splits.create_split(dataset_version_id, request.seed)
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/datasets/{dataset_version_id}/validation-report")
async def read_dataset_validation_report(dataset_version_id: str, database: DatabaseDep) -> Any:
    report = await TrainingRepository(database).latest_dataset_validation_report(dataset_version_id)
    if report is None:
        raise DevMindError("Dataset validation report not found", status.HTTP_404_NOT_FOUND)
    return report


@router.post("/configs/validate")
async def validate_training_config(
    request: Phase3TrainingConfig, orchestrator: TrainingDep, _: TrainingConfigureDep
) -> Any:
    return await orchestrator.configs.validate_and_save(request)


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_training_run(
    request: CreateTrainingRunRequest, orchestrator: TrainingDep, principal: TrainingConfigureDep
) -> Any:
    try:
        return await orchestrator.runs.create_run(
            request.training_config_id, principal.user.user_id
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/runs")
async def list_training_runs(database: DatabaseDep) -> Any:
    return {"training_runs": await TrainingRepository(database).list_training_runs()}


@router.get("/runs/{run_id}")
async def read_training_run(run_id: str, database: DatabaseDep) -> Any:
    run = await TrainingRepository(database).get_training_run(run_id)
    if run is None:
        raise DevMindError("Training run not found", status.HTTP_404_NOT_FOUND)
    return run


@router.post("/runs/{run_id}/cancel")
async def cancel_training_run(run_id: str, orchestrator: TrainingDep, _: TrainingCancelDep) -> Any:
    try:
        return await orchestrator.runs.cancel(run_id)
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/runs/{run_id}/smoke-train")
async def run_smoke_training(run_id: str, orchestrator: TrainingDep, _: TrainingStartDep) -> Any:
    try:
        return await orchestrator.runs.run_smoke_training(run_id)
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/runs/{run_id}/checkpoints")
async def read_checkpoints(run_id: str, database: DatabaseDep) -> Any:
    run = await TrainingRepository(database).get_training_run(run_id)
    if run is None:
        raise DevMindError("Training run not found", status.HTTP_404_NOT_FOUND)
    return {"checkpoints": run.checkpoints}


@router.get("/runs/{run_id}/metrics")
async def read_metrics(run_id: str, database: DatabaseDep) -> Any:
    run = await TrainingRepository(database).get_training_run(run_id)
    if run is None:
        raise DevMindError("Training run not found", status.HTTP_404_NOT_FOUND)
    return {"metrics_location": run.metrics_location, "current_step": run.current_step}


@router.post("/evaluations/baseline-unavailable")
async def record_baseline_unavailable(
    request: BaselineUnavailableRequest, orchestrator: TrainingDep, _: EvaluationStartDep
) -> Any:
    return await orchestrator.evaluations.record_baseline_unavailable(
        request.subject_id, request.evaluation_set_version, request.reason
    )


@router.post("/evaluations/candidate")
async def record_candidate_evaluation(
    request: CandidateEvaluationRequest, orchestrator: TrainingDep, _: EvaluationStartDep
) -> Any:
    return await orchestrator.evaluations.record_candidate_mock_evaluation(
        request.candidate_id, request.evaluation_set_version, request.scores
    )


@router.post("/candidates", status_code=status.HTTP_201_CREATED)
async def register_candidate(
    request: RegisterCandidateRequest, orchestrator: TrainingDep, principal: CandidateCreateDep
) -> Any:
    try:
        return await orchestrator.candidates.register(
            candidate_name=request.candidate_name,
            training_run_id=request.training_run_id,
            baseline_evaluation_id=request.baseline_evaluation_id,
            candidate_evaluation_id=request.candidate_evaluation_id,
            creator=principal.user.user_id,
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/candidates")
async def list_candidates(database: DatabaseDep) -> Any:
    return {"model_candidates": await TrainingRepository(database).list_phase3_model_candidates()}


@router.get("/candidates/{candidate_id}")
async def read_candidate(candidate_id: str, database: DatabaseDep) -> Any:
    candidate = await TrainingRepository(database).get_phase3_model_candidate(candidate_id)
    if candidate is None:
        raise DevMindError("Model candidate not found", status.HTTP_404_NOT_FOUND)
    return candidate


@router.post("/candidates/{candidate_id}/compare")
async def compare_candidate(
    candidate_id: str,
    request: CompareCandidateRequest,
    orchestrator: TrainingDep,
    _: CandidateReviewDep,
) -> Any:
    try:
        return await orchestrator.comparisons.compare(
            candidate_id, request.baseline_evaluation_id, request.candidate_evaluation_id
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/candidates/{candidate_id}/regression-report")
async def read_regression_report(candidate_id: str, database: DatabaseDep) -> Any:
    candidate = await TrainingRepository(database).get_phase3_model_candidate(candidate_id)
    if candidate is None:
        raise DevMindError("Model candidate not found", status.HTTP_404_NOT_FOUND)
    return candidate.regression_results


@router.post("/candidates/{candidate_id}/recommendation")
async def generate_recommendation(
    candidate_id: str, orchestrator: TrainingDep, _: CandidateReviewDep
) -> Any:
    try:
        return await orchestrator.recommendations.generate_for_candidate(
            orchestrator.training_repository, candidate_id
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/candidates/{candidate_id}/approve-for-manual-staging")
async def approve_for_manual_staging(
    candidate_id: str,
    request: ApprovalRequest,
    orchestrator: TrainingDep,
    principal: CandidateStageDep,
) -> Any:
    try:
        return await orchestrator.approvals.act(
            candidate_id=candidate_id,
            reviewer_id=principal.user.user_id,
            action=ModelApprovalAction.APPROVE_FOR_MANUAL_STAGING,
            notes=request.notes,
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/candidates/{candidate_id}/reject")
async def reject_candidate(
    candidate_id: str,
    request: ApprovalRequest,
    orchestrator: TrainingDep,
    principal: CandidateReviewDep,
) -> Any:
    try:
        return await orchestrator.approvals.act(
            candidate_id=candidate_id,
            reviewer_id=principal.user.user_id,
            action=ModelApprovalAction.REJECT,
            notes=request.notes,
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/candidates/{candidate_id}/request-more-evaluation")
async def request_more_evaluation(
    candidate_id: str,
    request: ApprovalRequest,
    orchestrator: TrainingDep,
    principal: CandidateReviewDep,
) -> Any:
    try:
        return await orchestrator.approvals.act(
            candidate_id=candidate_id,
            reviewer_id=principal.user.user_id,
            action=ModelApprovalAction.REQUEST_MORE_EVALUATION,
            notes=request.notes,
        )
    except TrainingServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/candidates/{candidate_id}/audit")
async def read_candidate_audit(candidate_id: str, database: DatabaseDep) -> Any:
    return {"actions": await TrainingRepository(database).list_model_approvals(candidate_id)}


@router.post("/candidates/{candidate_id}/adapter-load-check")
async def check_adapter_load(
    candidate_id: str, orchestrator: TrainingDep, _: CandidateReviewDep
) -> Any:
    return await orchestrator.adapter_loader.check(candidate_id)
