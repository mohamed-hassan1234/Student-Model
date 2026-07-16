from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from devmind_api.technology.curriculum import TechnologyTopic
from devmind_api.technology.models import (
    ContentType,
    EvidenceStatus,
    IngestionStatus,
    PermissionStatus,
    RagAnswer,
    RegisteredSource,
    ReviewStatus,
    SourceStatus,
    TrustLevel,
)


class Pagination(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RegisterSourceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=5, max_length=1000)
    original_url: HttpUrl
    content_type: ContentType
    technology_topic: TechnologyTopic
    subtopic: str | None = Field(default=None, max_length=120)
    trust_level: TrustLevel = TrustLevel.HIGH
    author_or_organization: str | None = Field(default=None, max_length=160)
    license_type: str = Field(min_length=2, max_length=80)
    license_url: HttpUrl | None = None
    license_review_status: ReviewStatus = ReviewStatus.PENDING
    retrieval_use_permission: PermissionStatus = PermissionStatus.ALLOWED
    training_use_permission: PermissionStatus = PermissionStatus.DISALLOWED
    human_approval_status: ReviewStatus = ReviewStatus.PENDING
    created_by: str = Field(default="local-admin", min_length=2, max_length=120)


class RegisterFileSourceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=5, max_length=1000)
    content_type: ContentType
    technology_topic: TechnologyTopic
    subtopic: str | None = Field(default=None, max_length=120)
    trust_level: TrustLevel = TrustLevel.HIGH
    author_or_organization: str | None = Field(default=None, max_length=160)
    license_type: str = Field(min_length=2, max_length=80)
    license_url: HttpUrl | None = None
    license_review_status: ReviewStatus = ReviewStatus.APPROVED
    retrieval_use_permission: PermissionStatus = PermissionStatus.ALLOWED
    training_use_permission: PermissionStatus = PermissionStatus.DISALLOWED
    human_approval_status: ReviewStatus = ReviewStatus.APPROVED
    created_by: str = Field(default="local-admin", min_length=2, max_length=120)


class SourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=1000)
    subtopic: str | None = Field(default=None, max_length=120)
    trust_level: TrustLevel | None = None
    license_url: HttpUrl | None = None
    retrieval_use_permission: PermissionStatus | None = None
    training_use_permission: PermissionStatus | None = None


class SourceReviewRequest(BaseModel):
    approved: bool
    reviewer: str = Field(default="local-admin", min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)


class DeactivateSourceRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class SourceListResponse(BaseModel):
    sources: list[RegisteredSource]
    limit: int
    offset: int


class IngestionStartRequest(BaseModel):
    source_id: str


class IngestionReportResponse(BaseModel):
    job_id: str
    document_id: str
    chunk_count: int
    content_hash: str


class AskTechnologyStudentRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    limit: int = Field(default=5, ge=1, le=10)


class AskTechnologyStudentResponse(RagAnswer):
    pass


class CurriculumTopicStatus(BaseModel):
    topic: TechnologyTopic
    available_source_count: int = 0
    ingested_document_count: int = 0
    coverage: str = "insufficient"


class CurriculumResponse(BaseModel):
    topics: list[CurriculumTopicStatus]


class CapabilityStatusResponse(BaseModel):
    student: str = "technology-student-v0.1"
    supported_content_types: list[ContentType]
    evidence_statuses: list[EvidenceStatus]
    source_statuses: list[SourceStatus]
    ingestion_statuses: list[IngestionStatus]
    paid_api_required: bool = False
    docker_required: bool = False
    training_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
