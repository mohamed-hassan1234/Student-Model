from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Difficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningCycleStatus(StrEnum):
    PLANNED = "planned"
    COLLECTING = "collecting"
    GENERATING = "generating"
    VERIFYING = "verifying"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuestionType(StrEnum):
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    EXAMPLE = "example"
    STEP_BY_STEP_TASK = "step_by_step_task"
    DEBUGGING = "debugging"
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_REVIEW = "code_review"
    SECURITY_REVIEW = "security_review"
    ARCHITECTURE = "architecture_question"
    SCENARIO = "scenario_question"
    MISCONCEPTION = "misconception_correction"
    ADVERSARIAL_MISCONCEPTION = "adversarial_misconception"
    UNSUPPORTED_DETECTION = "unsupported_question_detection"
    SOURCE_CONFLICT = "source_conflict_question"
    PRACTICAL_PROJECT = "practical_project_task"
    MULTIPLE_SOLUTION = "multiple_solution_question"


class ReviewQueueStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REGENERATION = "needs_regeneration"


class DatasetType(StrEnum):
    CONTINUED_PRETRAINING = "continued_pretraining"
    SFT = "sft"
    PREFERENCE = "preference"


class DatasetApprovalStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class CurriculumTopic(BaseModel):
    topic_id: str
    domain: str
    topic: str
    subtopic: str | None = None
    learning_objective: str
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: Difficulty
    importance: int = Field(ge=1, le=5)
    approved_source_count: int = 0
    ingested_document_count: int = 0
    verified_chunk_count: int = 0
    verified_question_count: int = 0
    evaluation_example_count: int = 0
    current_coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    current_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    known_knowledge_gaps: list[str] = Field(default_factory=list)
    last_learning_cycle: str | None = None
    next_recommended_learning_action: str = "collect_approved_sources"
    human_review_status: str = "pending"
    updated_at: datetime


class Curriculum(BaseModel):
    curriculum_id: str
    student_id: str = "technology-student-v0.1"
    version: str = "0.1"
    domains: list[str]
    topic_count: int
    created_at: datetime
    updated_at: datetime


class CoverageReport(BaseModel):
    curriculum_id: str
    overall_coverage_score: float = Field(ge=0.0, le=1.0)
    topic_scores: list[CurriculumTopic]
    insufficient_topics: list[str]


class KnowledgeGap(BaseModel):
    gap_id: str
    topic_id: str
    domain: str
    topic: str
    subtopic: str | None = None
    signals: list[str]
    severity: float = Field(ge=0.0, le=1.0)
    recommended_action: str
    status: str = "open"
    created_at: datetime
    updated_at: datetime


class LearningCycle(BaseModel):
    cycle_id: str
    domain: str
    topic: str
    objectives: list[str]
    source_set: list[str] = Field(default_factory=list)
    teacher_set: list[str] = Field(default_factory=lambda: ["mock"])
    question_generation_config: dict[str, Any] = Field(default_factory=dict)
    verification_thresholds: dict[str, float] = Field(default_factory=dict)
    maximum_examples: int = Field(default=10, ge=1, le=500)
    budget_limits: dict[str, int] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: LearningCycleStatus = LearningCycleStatus.PLANNED
    metrics: dict[str, Any] = Field(default_factory=dict)
    human_owner: str
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class GeneratedQuestion(BaseModel):
    question_id: str
    cycle_id: str | None = None
    domain: str
    topic: str
    subtopic: str | None = None
    learning_objective: str
    difficulty: Difficulty
    question_type: QuestionType
    source_basis: list[str]
    generator_provider: str
    generator_model: str
    generation_configuration: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    content_hash: str
    duplicate_status: str = "unique"
    review_status: ReviewQueueStatus = ReviewQueueStatus.PENDING
    question: str


class CandidateAnswer(BaseModel):
    candidate_id: str
    question_id: str
    teacher_provider: str
    teacher_model: str
    prompt_template_version: str
    source_context_ids: list[str]
    generated_answer: str
    generation_timestamp: datetime
    generation_configuration: dict[str, Any] = Field(default_factory=dict)
    content_hash: str
    verification_status: VerificationStatus = VerificationStatus.PENDING
    training_use_eligibility: bool = False


class VerificationSignal(BaseModel):
    signal_id: str
    candidate_id: str
    name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class VerificationRun(BaseModel):
    run_id: str
    candidate_id: str
    status: VerificationStatus
    signals: list[VerificationSignal]
    overall_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = True
    created_at: datetime


class ReviewItem(BaseModel):
    review_id: str
    candidate_id: str
    question_id: str
    status: ReviewQueueStatus = ReviewQueueStatus.PENDING
    reviewer_id: str | None = None
    reviewer_note: str | None = None
    rejection_reason: str | None = None
    edited_answer: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewerAction(BaseModel):
    action_id: str
    review_id: str
    reviewer_id: str
    action: str
    note: str | None = None
    created_at: datetime


class DatasetRecord(BaseModel):
    record_id: str
    dataset_candidate_id: str
    dataset_version: str | None = None
    dataset_type: DatasetType
    creation_timestamp: datetime
    domain: str
    topic: str
    subtopic: str | None = None
    source_provenance: list[dict[str, Any]]
    source_license_metadata: list[dict[str, Any]]
    retrieval_use_permission: str
    training_use_permission: str
    teacher_provenance: list[dict[str, Any]]
    teacher_output_training_permission: str
    verification_scores: dict[str, float]
    human_approval_status: ReviewQueueStatus
    reviewer_id: str | None = None
    review_timestamp: datetime | None = None
    rejection_reason: str | None = None
    edit_history: list[dict[str, Any]] = Field(default_factory=list)
    content_hash: str
    leakage_check: str = "not_evaluation_record"
    evaluation_set_exclusion_status: str = "excluded_from_evaluation"
    question: str | None = None
    answer: str | None = None
    text: str | None = None
    chosen: str | None = None
    rejected: str | None = None


class DatasetCandidate(BaseModel):
    dataset_candidate_id: str
    dataset_type: DatasetType
    status: DatasetApprovalStatus = DatasetApprovalStatus.DRAFT
    record_ids: list[str]
    created_at: datetime
    updated_at: datetime


class DatasetVersion(BaseModel):
    dataset_version_id: str
    name: str
    description: str
    dataset_type: DatasetType
    parent_version: str | None = None
    creation_timestamp: datetime
    creator: str
    approved_record_count: int
    rejected_record_count: int
    domain_distribution: dict[str, int]
    topic_distribution: dict[str, int]
    difficulty_distribution: dict[str, int]
    source_distribution: dict[str, int]
    teacher_distribution: dict[str, int]
    license_summary: dict[str, int]
    verification_summary: dict[str, float]
    content_manifest_hash: str
    export_file_hash: str | None = None
    evaluation_exclusion_checks: str
    approval_status: DatasetApprovalStatus
    approver: str | None = None
    approval_timestamp: datetime | None = None
    immutable: bool = True


class EvaluationRecord(BaseModel):
    evaluation_record_id: str
    category: str
    prompt: str
    expected_behavior: str
    source_ids: list[str] = Field(default_factory=list)
    content_hash: str
    created_at: datetime


class EvaluationSet(BaseModel):
    evaluation_set_id: str
    version: str
    categories: list[str]
    record_ids: list[str]
    frozen: bool = True
    created_at: datetime


class TrainingConfig(BaseModel):
    training_config_id: str
    base_model_identifier: str
    base_model_revision: str
    base_model_license: str
    tokenizer_identifier: str
    tokenizer_revision: str
    dataset_version: str
    evaluation_set_version: str
    training_method: Literal["lora", "peft", "mock_dry_run"]
    lora_configuration: dict[str, Any] = Field(default_factory=dict)
    quantization_configuration: dict[str, Any] = Field(default_factory=dict)
    batch_settings: dict[str, Any] = Field(default_factory=dict)
    learning_rate: float = Field(gt=0.0, le=1.0)
    epochs: int = Field(ge=1, le=100)
    sequence_length: int = Field(ge=64, le=32768)
    seed: int = Field(ge=0)
    output_directory: str
    logging_directory: str
    hardware_requirements: dict[str, Any] = Field(default_factory=dict)
    resume_configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def prevent_overwrite_paths(self) -> "TrainingConfig":
        if self.output_directory == self.logging_directory:
            raise ValueError("Training output and logging directories must be different")
        return self


class ModelCandidate(BaseModel):
    candidate_id: str
    base_model: str
    base_model_revision: str
    base_model_license: str
    adapter_location: str
    adapter_hash: str
    training_config_version: str
    dataset_version: str
    evaluation_set_version: str
    training_metrics: dict[str, float] = Field(default_factory=dict)
    evaluation_metrics: dict[str, float] = Field(default_factory=dict)
    safety_metrics: dict[str, float] = Field(default_factory=dict)
    regression_results: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    creator: str
    approval_state: DatasetApprovalStatus = DatasetApprovalStatus.PENDING
    deployment_recommendation: str = "not_recommended"
    rollback_metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentRecommendation(BaseModel):
    candidate_id: str
    recommended: bool
    reasons: list[str]
    created_at: datetime


def learning_document(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python")
