from devmind_api.technology.chunking import Chunker
from devmind_api.technology.embeddings import EmbeddingRequest, MockEmbeddingProvider
from devmind_api.technology.models import (
    ContentType,
    IngestionStatus,
    ParsedDocument,
    PermissionStatus,
    RegisteredSource,
    ReviewStatus,
    SourceStatus,
    TrustLevel,
)
from devmind_api.technology.vector_search import (
    DeterministicMockVectorSearchProvider,
    IndexedVector,
    LocalFaissFallbackProvider,
    MongoVectorSearchProvider,
    VectorProviderError,
)
from devmind_shared.time import utc_now


def _source() -> RegisteredSource:
    now = utc_now()
    return RegisteredSource(
        source_id="src_test",
        name="React docs",
        description="Approved React documentation",
        original_reference="https://react.dev/learn",
        source_domain="react.dev",
        content_type=ContentType.MARKDOWN,
        technology_topic="react",
        trust_level=TrustLevel.OFFICIAL,
        license_type="mit",
        license_review_status=ReviewStatus.APPROVED,
        retrieval_use_permission=PermissionStatus.ALLOWED,
        training_use_permission=PermissionStatus.DISALLOWED,
        human_approval_status=ReviewStatus.APPROVED,
        date_added=now,
        source_status=SourceStatus.ACTIVE,
        ingestion_status=IngestionStatus.NOT_STARTED,
        created_by="test",
        created_at=now,
        updated_at=now,
    )


async def test_chunking_is_deterministic_and_deduplicates() -> None:
    source = _source()
    parsed = ParsedDocument(
        title="React",
        content_type=ContentType.MARKDOWN,
        text=("React components render UI.\n\n" * 20).strip(),
        sections=["React"],
    )
    chunker = Chunker(chunk_size=220, overlap=20)

    first = chunker.chunk(source, parsed, "doc1", "docv1")
    second = chunker.chunk(source, parsed, "doc1", "docv1")

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]
    assert len({chunk.content_hash for chunk in first}) == len(first)


async def test_mock_embeddings_are_deterministic() -> None:
    provider = MockEmbeddingProvider(dimensions=8)

    first = await provider.embed(EmbeddingRequest("MongoDB stores documents"))
    second = await provider.embed(EmbeddingRequest("MongoDB stores documents"))

    assert first.vector == second.vector
    assert first.dimensions == 8


async def test_mock_vector_search_ranks_candidates() -> None:
    source = _source()
    parsed = ParsedDocument(
        title="Git", content_type=ContentType.TEXT, text="Git commits track snapshots."
    )
    chunk = Chunker(chunk_size=200, overlap=0).chunk(source, parsed, "doc", "docv")[0]
    provider = DeterministicMockVectorSearchProvider(
        [IndexedVector(chunk=chunk, vector=[1.0, 0.0])]
    )

    results = await provider.search([1.0, 0.0], limit=1)

    assert results[0].chunk.chunk_id == chunk.chunk_id
    assert results[0].score == 1.0


async def test_local_faiss_fallback_rebuilds_from_vectors(tmp_path) -> None:  # type: ignore[no-untyped-def]
    source = _source()
    parsed = ParsedDocument(
        title="Git", content_type=ContentType.TEXT, text="Git commits track snapshots."
    )
    chunk = Chunker(chunk_size=200, overlap=0).chunk(source, parsed, "doc", "docv")[0]
    provider = LocalFaissFallbackProvider(tmp_path / "devmind.faiss.json")

    await provider.rebuild([IndexedVector(chunk=chunk, vector=[1.0, 0.0])])
    results = await provider.search([1.0, 0.0], limit=1)

    assert results[0].chunk.chunk_id == chunk.chunk_id


async def test_mongodb_vector_adapter_reports_unavailable() -> None:
    class BrokenCollection:
        def aggregate(self, pipeline):  # type: ignore[no-untyped-def]
            raise RuntimeError("no vector index")

    class BrokenDatabase:
        def __getitem__(self, name: str) -> BrokenCollection:
            return BrokenCollection()

    provider = MongoVectorSearchProvider(BrokenDatabase())  # type: ignore[arg-type]

    try:
        await provider.search([1.0], limit=1)
    except VectorProviderError as exc:
        assert "unavailable" in str(exc)
    else:
        raise AssertionError("Expected vector provider error")
