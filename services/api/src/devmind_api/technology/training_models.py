from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ManifestReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TrainingRunStatus(StrEnum):
    PLANNED = "planned"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class DeploymentRecommendationStatus(StrEnum):
    RECOMMENDED_FOR_MANUAL_STAGING = "recommended_for_manual_staging"
    NEEDS_MORE_EVALUATION = "needs_more_evaluation"
    REJECTED_FOR_REGRESSION = "rejected_for_regression"
    REJECTED_FOR_SAFETY = "rejected_for_safety"
    REJECTED_FOR_LICENSE = "rejected_for_license"
    REJECTED_FOR_DATASET_INTEGRITY = "rejected_for_dataset_integrity"
    REJECTED_FOR_RESOURCE_REQUIREMENTS = "rejected_for_resource_requirements"


class ModelApprovalAction(StrEnum):
    APPROVE_FOR_MANUAL_STAGING = "approve_for_manual_staging"
    REJECT = "reject"
    REQUEST_MORE_EVALUATION = "request_more_evaluation"


class BaseModelManifest(BaseModel):
    manifest_id: str
    model_identifier: str = Field(min_length=2)
    exact_revision: str = Field(min_length=4)
    model_family: str
    parameter_count: str
    architecture: str
    tokenizer_identifier: str
    tokenizer_revision: str = Field(min_length=4)
    context_length: int = Field(ge=128)
    license_name: str
    license_reference: str
    commercial_use_status: str
    fine_tuning_permission: str
    redistribution_status: str
    required_trust_remote_code: bool = False
    trust_remote_code_approved: bool = False
    expected_memory_gb: float = Field(ge=0.0)
    expected_disk_gb: float = Field(ge=0.0)
    minimum_recommended_hardware: dict[str, Any] = Field(default_factory=dict)
    hashes: dict[str, str] = Field(default_factory=dict)
    human_license_review_status: ManifestReviewStatus = ManifestReviewStatus.PENDING
    approval_status: ManifestReviewStatus = ManifestReviewStatus.PENDING
    created_by: str
    created_at: datetime
    updated_at: datetime

    @field_validator("exact_revision", "tokenizer_revision")
    @classmethod
    def reject_floating_revisions(cls, value: str) -> str:
        floating = {"main", "master", "latest", "dev", "stable", "HEAD"}
        if value.strip() in floating:
            raise ValueError("Model and tokenizer revisions must be pinned to exact revisions")
        return value


class HardwareCapabilityReport(BaseModel):
    report_id: str
    operating_system: str
    python_version: str
    cpu: str
    system_ram_gb: float
    gpu_available: bool
    gpu_name: str | None = None
    gpu_memory_gb: float | None = None
    cuda_available: bool
    supported_precision: list[str]
    available_disk_gb: float
    recommended_training_mode: str
    expected_limitations: list[str]
    created_at: datetime


class DatasetValidationReport(BaseModel):
    report_id: str
    dataset_version_id: str
    valid: bool
    approved_record_count: int
    rejected_record_count: int
    training_count: int
    validation_count: int
    held_out_test_count: int
    topic_distribution: dict[str, int]
    difficulty_distribution: dict[str, int]
    source_distribution: dict[str, int]
    license_distribution: dict[str, int]
    teacher_distribution: dict[str, int]
    average_input_length: float
    average_output_length: float
    maximum_sequence_length: int
    duplicate_statistics: dict[str, Any]
    leakage_statistics: dict[str, Any]
    secret_scan_result: str
    estimated_token_count: int
    estimated_hardware_requirement: dict[str, Any]
    blocking_issues: list[str] = Field(default_factory=list)
    created_at: datetime


class DatasetSplitItem(BaseModel):
    record_id: str
    split: Literal["train", "validation", "held_out_test"]
    group_id: str
    content_hash: str


class DatasetSplitManifest(BaseModel):
    split_manifest_id: str
    dataset_version_id: str
    seed: int
    train_count: int
    validation_count: int
    held_out_test_count: int
    items: list[DatasetSplitItem]
    manifest_hash: str
    created_at: datetime


class Phase3TrainingConfig(BaseModel):
    training_config_id: str
    experiment_name: str
    base_model_manifest_id: str
    dataset_version_id: str
    split_manifest_id: str
    evaluation_set_version: str
    training_method: Literal["lora", "qlora", "mock_smoke"]
    lora_rank: int = Field(default=8, ge=1, le=256)
    lora_alpha: int = Field(default=16, ge=1, le=512)
    lora_dropout: float = Field(default=0.05, ge=0.0, le=0.9)
    target_modules: list[str] = Field(default_factory=lambda: ["q_proj", "v_proj"])
    bias: Literal["none", "all", "lora_only"] = "none"
    learning_rate: float = Field(default=0.0002, gt=0.0, le=1.0)
    optimizer: str = "adamw_torch"
    scheduler: str = "cosine"
    warmup_steps: int = Field(default=0, ge=0)
    epochs: int = Field(default=1, ge=1, le=100)
    batch_size: int = Field(default=1, ge=1, le=1024)
    gradient_accumulation_steps: int = Field(default=1, ge=1, le=1024)
    maximum_sequence_length: int = Field(default=1024, ge=64, le=32768)
    gradient_checkpointing: bool = False
    precision: Literal["fp32", "fp16", "bf16"] = "fp32"
    quantization_mode: Literal["none", "4bit", "8bit"] = "none"
    seed: int = Field(default=7, ge=0)
    logging_interval: int = Field(default=10, ge=1)
    evaluation_interval: int = Field(default=100, ge=1)
    checkpoint_interval: int = Field(default=100, ge=1)
    early_stopping: dict[str, Any] = Field(default_factory=dict)
    output_directory: str
    resume_checkpoint: str | None = None
    hardware_requirements: dict[str, Any] = Field(default_factory=dict)
    maximum_runtime_minutes: int | None = Field(default=None, ge=1)
    created_at: datetime

    @model_validator(mode="after")
    def validate_quantization(self) -> "Phase3TrainingConfig":
        if self.training_method == "qlora" and self.quantization_mode == "none":
            raise ValueError("QLoRA requires an explicit quantization mode")
        if self.training_method != "qlora" and self.quantization_mode != "none":
            raise ValueError("Quantization is only supported for qlora configurations")
        return self


class TrainingArtifact(BaseModel):
    artifact_id: str
    training_run_id: str
    artifact_type: str
    path: str
    sha256: str
    size_bytes: int
    created_at: datetime


class CheckpointMetadata(BaseModel):
    checkpoint_id: str
    training_run_id: str
    path: str
    sha256: str
    step: int
    compatible: bool = True
    created_at: datetime


class TrainingRun(BaseModel):
    run_id: str
    experiment_name: str
    status: TrainingRunStatus
    base_model_manifest_id: str
    base_model_identifier: str
    base_model_revision: str
    base_model_license: str
    dataset_version: str
    dataset_hash: str
    split_manifest_hash: str
    evaluation_set_version: str
    training_config_version: str
    effective_configuration: dict[str, Any]
    host_information: dict[str, Any]
    hardware_information: dict[str, Any]
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    current_step: int = 0
    epoch: float = 0.0
    checkpoints: list[CheckpointMetadata] = Field(default_factory=list)
    adapter_location: str | None = None
    adapter_hash: str | None = None
    metrics_location: str | None = None
    logs_location: str | None = None
    failure_category: str | None = None
    safe_error_summary: str | None = None
    creator: str
    human_approval_state: ManifestReviewStatus = ManifestReviewStatus.PENDING
    created_at: datetime
    updated_at: datetime


class ModelEvaluation(BaseModel):
    evaluation_id: str
    subject_id: str
    subject_type: Literal["base_model", "candidate_adapter", "production_model"]
    evaluation_set_version: str
    scores: dict[str, float]
    latency_ms: float | None = None
    memory_mb: float | None = None
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    unavailable_reason: str | None = None
    created_at: datetime


class CandidateComparison(BaseModel):
    comparison_id: str
    candidate_id: str
    baseline_evaluation_id: str
    candidate_evaluation_id: str
    overall_improvement: float
    domain_improvements: dict[str, float]
    domain_regressions: dict[str, float]
    safety_changes: dict[str, float]
    citation_change: float
    performance_changes: dict[str, float]
    resource_changes: dict[str, float]
    blocking_regressions: list[str]
    recommendation: DeploymentRecommendationStatus
    created_at: datetime


class Phase3ModelCandidate(BaseModel):
    candidate_id: str
    candidate_name: str
    base_model_manifest_id: str
    base_model_revision: str
    adapter_location: str
    adapter_hash: str
    training_run_id: str
    training_config_version: str
    dataset_version: str
    evaluation_set_version: str
    baseline_results: dict[str, float]
    candidate_results: dict[str, float]
    regression_results: dict[str, Any]
    safety_status: str
    license_status: str
    created_at: datetime
    creator: str
    approval_state: ManifestReviewStatus = ManifestReviewStatus.PENDING
    deployment_recommendation: DeploymentRecommendationStatus = (
        DeploymentRecommendationStatus.NEEDS_MORE_EVALUATION
    )
    rollback_information: dict[str, Any]


class Phase3DeploymentRecommendation(BaseModel):
    recommendation_id: str
    candidate_id: str
    recommendation: DeploymentRecommendationStatus
    reasons: list[str]
    created_at: datetime


class ModelApproval(BaseModel):
    approval_id: str
    candidate_id: str
    reviewer_id: str
    action: ModelApprovalAction
    reviewer_notes: str | None = None
    created_at: datetime


class AdapterLoadCheck(BaseModel):
    candidate_id: str
    loadable: bool
    provider: str
    status: str
    reasons: list[str]
    checked_at: datetime


def training_document(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python")
