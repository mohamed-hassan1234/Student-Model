from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(StrEnum):
    HTML = "text/html"
    PDF = "application/pdf"
    MARKDOWN = "text/markdown"
    TEXT = "text/plain"


class TrustLevel(StrEnum):
    OFFICIAL = "official"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PermissionStatus(StrEnum):
    ALLOWED = "allowed"
    DISALLOWED = "disallowed"
    UNKNOWN = "unknown"


class SourceStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class IngestionStatus(StrEnum):
    NOT_STARTED = "not_started"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvidenceStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


class PromptInjectionFlags(BaseModel):
    has_instruction_override: bool = False
    asks_for_secrets: bool = False
    asks_for_policy_change: bool = False
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)


class RegisteredSource(BaseModel):
    source_id: str
    name: str
    description: str
    original_reference: str
    source_domain: str
    content_type: ContentType
    technology_topic: str
    subtopic: str | None = None
    trust_level: TrustLevel
    author_or_organization: str | None = None
    license_type: str
    license_url: str | None = None
    license_review_status: ReviewStatus
    retrieval_use_permission: PermissionStatus
    training_use_permission: PermissionStatus
    human_approval_status: ReviewStatus
    date_added: datetime
    date_last_checked: datetime | None = None
    content_checksum: str | None = None
    source_status: SourceStatus
    ingestion_status: IngestionStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    deactivation_reason: str | None = None


class ParsedDocument(BaseModel):
    title: str
    content_type: ContentType
    text: str
    sections: list[str] = Field(default_factory=list)
    canonical_url: str | None = None
    page_count: int | None = None
    empty_pages: list[int] = Field(default_factory=list)
    extraction_warnings: list[str] = Field(default_factory=list)
    prompt_injection_flags: PromptInjectionFlags = Field(default_factory=PromptInjectionFlags)


class DocumentChunk(BaseModel):
    chunk_id: str
    source_id: str
    document_id: str
    document_version_id: str
    original_reference: str
    document_title: str
    section_heading: str | None = None
    page_number: int | None = None
    chunk_number: int
    character_start: int
    character_end: int
    token_estimate: int
    text: str
    content_hash: str
    trust_level: TrustLevel
    license_status: ReviewStatus
    retrieval_use_status: PermissionStatus
    training_use_status: PermissionStatus
    prompt_injection_flags: PromptInjectionFlags
    ingestion_timestamp: datetime


class EmbeddedChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_id: str
    embedding_provider: str
    embedding_model: str
    embedding_model_version: str | None = None
    embedding_dimensions: int
    vector: list[float]
    content_hash: str
    created_at: datetime
    reembedding_status: str = "current"


class RetrievalCandidate(BaseModel):
    chunk: DocumentChunk
    score: float


class Citation(BaseModel):
    source_id: str
    document_id: str
    title: str
    url: str | None
    section: str | None
    page: int | None
    relevance_score: float


class RagAnswer(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    topic: str | None
    sources: list[Citation]
    limitations: list[str]
    evidence_status: EvidenceStatus


def document_to_mongo(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python")
