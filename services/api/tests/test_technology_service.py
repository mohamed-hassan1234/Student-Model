from fakes import FakeMongoDatabase

from devmind_api.config import Settings
from devmind_api.technology.models import (
    ContentType,
    EvidenceStatus,
    PermissionStatus,
    ReviewStatus,
    TrustLevel,
)
from devmind_api.technology.repositories import TechnologyRepository
from devmind_api.technology.services import SourceRegistration, TechnologyStudentService


def _registration() -> SourceRegistration:
    return SourceRegistration(
        name="React Source",
        description="Approved React source",
        original_reference="https://react.dev/learn",
        content_type=ContentType.MARKDOWN,
        technology_topic="react",
        subtopic="components",
        trust_level=TrustLevel.OFFICIAL,
        author_or_organization="React",
        license_type="mit",
        license_url=None,
        license_review_status=ReviewStatus.APPROVED,
        retrieval_use_permission=PermissionStatus.ALLOWED,
        training_use_permission=PermissionStatus.DISALLOWED,
        human_approval_status=ReviewStatus.APPROVED,
        created_by="test",
    )


async def test_ingestion_and_rag_answer_with_citations() -> None:
    database = FakeMongoDatabase()
    settings = Settings(
        INGESTION_CHUNK_SIZE=400, INGESTION_CHUNK_OVERLAP=0, EMBEDDING_DIMENSIONS=16
    )
    service = TechnologyStudentService(TechnologyRepository(database), settings)
    source = await service.register_source(_registration())

    report = await service.ingest_source_bytes(
        source.source_id,
        b"# React components\n\nReact components are JavaScript functions that return UI.",
    )
    answer = await service.answer_question("What are React components?")

    assert report["chunk_count"] >= 1
    assert answer.evidence_status is EvidenceStatus.SUPPORTED
    assert answer.sources[0].source_id == source.source_id


async def test_unsupported_question_returns_insufficient_evidence() -> None:
    database = FakeMongoDatabase()
    service = TechnologyStudentService(TechnologyRepository(database), Settings())

    answer = await service.answer_question("Explain quantum compilers")

    assert answer.evidence_status is EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert answer.sources == []
