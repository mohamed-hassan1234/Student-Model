import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import cast

from devmind_api.config import Settings
from devmind_api.technology.chunking import Chunker, chunk_is_retrievable
from devmind_api.technology.curriculum import classify_question
from devmind_api.technology.embeddings import (
    EmbeddingProvider,
    EmbeddingRequest,
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
)
from devmind_api.technology.hashing import sha256_hex, stable_id
from devmind_api.technology.models import (
    Citation,
    ContentType,
    DocumentChunk,
    EmbeddedChunk,
    EvidenceStatus,
    IngestionStatus,
    PermissionStatus,
    RagAnswer,
    RegisteredSource,
    ReviewStatus,
    SourceStatus,
    TrustLevel,
)
from devmind_api.technology.parsers import parse_document
from devmind_api.technology.policy import (
    assert_can_ingest_source,
    assert_domain_allowed,
    validate_source_registration,
)
from devmind_api.technology.repositories import TechnologyRepository
from devmind_api.technology.security import (
    infer_content_type_from_filename,
    validate_http_url,
    validate_upload_bytes,
)
from devmind_model_gateway.providers import (
    LlamaCppHttpModelProvider,
    MockModelProvider,
    ModelProvider,
    OllamaModelProvider,
    ProviderRequest,
    VllmHttpModelProvider,
)
from devmind_shared.time import utc_now


class TechnologyServiceError(ValueError):
    pass


@dataclass(frozen=True)
class SourceRegistration:
    name: str
    description: str
    original_reference: str
    content_type: ContentType
    technology_topic: str
    subtopic: str | None
    trust_level: TrustLevel
    author_or_organization: str | None
    license_type: str
    license_url: str | None
    license_review_status: ReviewStatus
    retrieval_use_permission: PermissionStatus
    training_use_permission: PermissionStatus
    human_approval_status: ReviewStatus
    created_by: str


class TechnologyStudentService:
    def __init__(
        self,
        repository: TechnologyRepository,
        settings: Settings,
        embedding_provider: EmbeddingProvider | None = None,
        model_provider: ModelProvider | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._embedding_provider = embedding_provider or build_embedding_provider(settings)
        self._model_provider = model_provider or build_model_provider(settings)

    async def register_source(self, registration: SourceRegistration) -> RegisteredSource:
        domain = validate_source_registration(
            original_reference=registration.original_reference,
            technology_topic=registration.technology_topic,
            license_type=registration.license_type,
            retrieval_use_permission=registration.retrieval_use_permission,
            training_use_permission=registration.training_use_permission,
        )
        now = utc_now()
        approved = (
            registration.license_review_status is ReviewStatus.APPROVED
            and registration.human_approval_status is ReviewStatus.APPROVED
        )
        source = RegisteredSource(
            source_id=stable_id("src", f"{registration.original_reference}:{registration.name}"),
            name=registration.name,
            description=registration.description,
            original_reference=registration.original_reference,
            source_domain=domain,
            content_type=registration.content_type,
            technology_topic=registration.technology_topic,
            subtopic=registration.subtopic,
            trust_level=registration.trust_level,
            author_or_organization=registration.author_or_organization,
            license_type=registration.license_type,
            license_url=registration.license_url,
            license_review_status=registration.license_review_status,
            retrieval_use_permission=registration.retrieval_use_permission,
            training_use_permission=registration.training_use_permission,
            human_approval_status=registration.human_approval_status,
            date_added=now,
            date_last_checked=None,
            content_checksum=None,
            source_status=SourceStatus.APPROVED if approved else SourceStatus.PENDING_REVIEW,
            ingestion_status=IngestionStatus.NOT_STARTED,
            created_by=registration.created_by,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create_source(source)

    async def approve_source(
        self, source_id: str, reviewer: str, approved: bool, notes: str | None
    ) -> RegisteredSource:
        source = await self._repository.get_source(source_id)
        if source is None:
            raise TechnologyServiceError("Source not found")
        status = SourceStatus.APPROVED if approved else SourceStatus.REJECTED
        review_status = ReviewStatus.APPROVED if approved else ReviewStatus.REJECTED
        await self._repository.record_source_review(source_id, reviewer, review_status.value, notes)
        updated = await self._repository.update_source(
            source_id,
            {
                "source_status": status.value,
                "human_approval_status": review_status.value,
            },
        )
        if updated is None:
            raise TechnologyServiceError("Source not found after update")
        return updated

    async def ingest_source_bytes(self, source_id: str, data: bytes) -> dict[str, object]:
        source = await self._repository.get_source(source_id)
        if source is None:
            raise TechnologyServiceError("Source not found")
        assert_can_ingest_source(source)
        assert_domain_allowed(source)
        validate_upload_bytes(data, self._settings.max_upload_bytes)
        return await self._ingest_bytes(source, data)

    async def ingest_source_url(self, source_id: str) -> dict[str, object]:
        source = await self._repository.get_source(source_id)
        if source is None:
            raise TechnologyServiceError("Source not found")
        assert_can_ingest_source(source)
        safe_url = validate_http_url(source.original_reference)
        if safe_url.domain != source.source_domain:
            raise TechnologyServiceError("Source domain mismatch")
        data = _fetch_url(source.original_reference, self._settings.max_web_fetch_bytes)
        return await self._ingest_bytes(source, data)

    async def upload_and_register(
        self,
        *,
        filename: str,
        data: bytes,
        registration: SourceRegistration,
    ) -> RegisteredSource:
        validate_upload_bytes(data, self._settings.max_upload_bytes)
        inferred_type = infer_content_type_from_filename(filename)
        if inferred_type is not registration.content_type:
            raise TechnologyServiceError("Filename extension does not match declared content type")
        checksum = sha256_hex(data)
        source = await self.register_source(registration)
        await self._repository.update_source(
            source.source_id,
            {
                "content_checksum": checksum,
                "original_reference": f"file-id://{source.source_id}",
            },
        )
        return source

    async def _ingest_bytes(self, source: RegisteredSource, data: bytes) -> dict[str, object]:
        job_id = await self._repository.create_ingestion_job(source.source_id, "system")
        await self._repository.update_ingestion_job(
            job_id,
            {"state": "running", "started_at": utc_now(), "attempts": 1},
        )
        try:
            parsed = parse_document(source.content_type, data, source.original_reference)
            content_hash = sha256_hex(parsed.text)
            document_id = stable_id("doc", f"{source.source_id}:{content_hash}")
            document_version_id = stable_id("docv", f"{document_id}:{content_hash}")
            chunker = Chunker(
                self._settings.ingestion_chunk_size, self._settings.ingestion_chunk_overlap
            )
            chunks = chunker.chunk(source, parsed, document_id, document_version_id)
            embeddings: list[EmbeddedChunk] = []
            for chunk in chunks:
                result = await self._embedding_provider.embed(EmbeddingRequest(chunk.text))
                if result.dimensions != self._settings.embedding_dimensions:
                    raise TechnologyServiceError("Embedding dimension mismatch")
                embeddings.append(
                    EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        document_id=document_id,
                        source_id=source.source_id,
                        embedding_provider=result.provider,
                        embedding_model=result.model,
                        embedding_model_version=result.model_version,
                        embedding_dimensions=result.dimensions,
                        vector=result.vector,
                        content_hash=chunk.content_hash,
                        created_at=utc_now(),
                    )
                )
            await self._repository.create_document_with_chunks(
                source=source,
                document_id=document_id,
                document_version_id=document_version_id,
                title=parsed.title,
                content_hash=content_hash,
                chunks=chunks,
                embeddings=embeddings,
                extraction_warnings=parsed.extraction_warnings,
            )
            await self._repository.update_ingestion_job(
                job_id,
                {"state": "completed", "completed_at": utc_now()},
            )
            await self._repository.record_ingestion_event(
                job_id,
                source.source_id,
                "completed",
                "Ingestion completed",
                {"chunk_count": len(chunks), "document_id": document_id},
            )
            return {
                "job_id": job_id,
                "document_id": document_id,
                "chunk_count": len(chunks),
                "content_hash": content_hash,
            }
        except Exception as exc:
            await self._repository.update_ingestion_job(
                job_id,
                {
                    "state": "failed",
                    "completed_at": utc_now(),
                    "error_category": exc.__class__.__name__,
                    "safe_error_summary": str(exc)[:300],
                },
            )
            await self._repository.record_ingestion_event(
                job_id,
                source.source_id,
                "failed",
                "Ingestion failed safely",
                {"error_category": exc.__class__.__name__},
            )
            raise

    async def answer_question(self, question: str, limit: int = 5) -> RagAnswer:
        if len(question.strip()) < 3:
            raise TechnologyServiceError("Question is too short")
        topic = classify_question(question)
        query_embedding = await self._embedding_provider.embed(EmbeddingRequest(question))
        stored_chunks = await self._repository.find_chunks_by_topic(
            topic.value if topic else None, limit=100
        )
        candidates = []
        for document in stored_chunks:
            chunk = document["chunk"]
            embedding = document["embedding"]
            if embedding["embedding_dimensions"] != query_embedding.dimensions:
                continue
            from devmind_api.technology.vector_search import _cosine_similarity

            parsed_chunk = DocumentChunk.model_validate(chunk)
            if not chunk_is_retrievable(parsed_chunk):
                continue
            vector_score = _cosine_similarity(query_embedding.vector, embedding["vector"])
            keyword_score = _keyword_overlap(question, parsed_chunk.text)
            candidates.append((parsed_chunk, max(vector_score, keyword_score)))
        ranked = sorted(candidates, key=lambda item: item[1], reverse=True)[:limit]
        if not ranked or ranked[0][1] < 0.05:
            answer = RagAnswer(
                answer="I do not have enough approved evidence to answer that as a verified fact.",
                confidence=0.0,
                topic=topic.value if topic else None,
                sources=[],
                limitations=["No sufficiently relevant approved chunks were retrieved."],
                evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
            )
            await self._repository.record_retrieval_event(
                question=question,
                topic=topic.value if topic else None,
                answer=answer,
                chunk_ids=[],
            )
            return answer
        context_lines = []
        citations: list[Citation] = []
        for chunk, score in ranked:
            context_lines.append(f"[{chunk.chunk_id}] Source content, untrusted:\n{chunk.text}\n")
            citations.append(
                Citation(
                    source_id=chunk.source_id,
                    document_id=chunk.document_id,
                    title=chunk.document_title,
                    url=chunk.original_reference
                    if chunk.original_reference.startswith("http")
                    else None,
                    section=chunk.section_heading,
                    page=chunk.page_number,
                    relevance_score=round(float(score), 4),
                )
            )
        prompt = (
            "Answer only from the provided untrusted source excerpts. "
            "If the excerpts do not support a claim, say so.\n\n"
            + "\n".join(context_lines)
            + f"\nQuestion: {question}"
        )
        response = await self._model_provider.generate(
            ProviderRequest(
                prompt=prompt, system_prompt="You are Technology Student v0.1.", max_tokens=256
            )
        )
        confidence = max(0.1, min(0.95, ranked[0][1]))
        answer = RagAnswer(
            answer=response.text,
            confidence=confidence,
            topic=topic.value if topic else None,
            sources=citations,
            limitations=["Answers are grounded only in retrieved approved source chunks."],
            evidence_status=EvidenceStatus.SUPPORTED,
        )
        await self._repository.record_retrieval_event(
            question=question,
            topic=topic.value if topic else None,
            answer=answer,
            chunk_ids=[chunk.chunk_id for chunk, _ in ranked],
        )
        return answer


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider(settings.embedding_model_name, settings.embedding_dimensions)
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(
            settings.local_model_base_url,
            settings.embedding_model_name,
            settings.embedding_dimensions,
            settings.model_provider_timeout_seconds,
        )
    raise TechnologyServiceError("Unsupported embedding provider")


def build_model_provider(settings: Settings) -> ModelProvider:
    if settings.local_model_provider == "mock":
        return MockModelProvider()
    if settings.local_model_provider == "ollama":
        return OllamaModelProvider(
            settings.local_model_base_url,
            settings.local_model_name,
            settings.model_provider_timeout_seconds,
        )
    if settings.local_model_provider == "llama_cpp":
        return LlamaCppHttpModelProvider(
            settings.local_model_base_url,
            settings.local_model_name,
            settings.model_provider_timeout_seconds,
        )
    if settings.local_model_provider == "vllm":
        return VllmHttpModelProvider(
            settings.local_model_base_url,
            settings.local_model_name,
            settings.model_provider_timeout_seconds,
        )
    raise TechnologyServiceError("Unsupported model provider")


def _fetch_url(url: str, max_bytes: int) -> bytes:
    request = urllib.request.Request(  # noqa: S310 - URL is validated before fetch.
        url,
        headers={"user-agent": "DevMindAI/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            data = response.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise TechnologyServiceError("Web source could not be fetched safely") from exc
    if len(data) > max_bytes:
        raise TechnologyServiceError("Web source exceeds configured fetch size")
    return cast(bytes, data)


def _keyword_overlap(question: str, text: str) -> float:
    question_terms = {term for term in question.lower().split() if len(term) > 2}
    text_terms = {term.strip(".,:;()[]{}").lower() for term in text.split() if len(term) > 2}
    if not question_terms:
        return 0.0
    return len(question_terms & text_terms) / len(question_terms)
