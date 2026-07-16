import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from devmind_api.db import MongoDatabase
from devmind_api.technology.models import DocumentChunk, RetrievalCandidate


class VectorProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class IndexedVector:
    chunk: DocumentChunk
    vector: list[float]


class VectorSearchProvider(Protocol):
    provider_name: str

    async def search(self, query_vector: list[float], limit: int) -> list[RetrievalCandidate]:
        """Search for nearest chunks."""


class DeterministicMockVectorSearchProvider:
    provider_name = "mock"

    def __init__(self, indexed_vectors: list[IndexedVector] | None = None) -> None:
        self._indexed_vectors = indexed_vectors or []

    async def search(self, query_vector: list[float], limit: int) -> list[RetrievalCandidate]:
        ranked = [
            RetrievalCandidate(
                chunk=item.chunk, score=_cosine_similarity(query_vector, item.vector)
            )
            for item in self._indexed_vectors
        ]
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:limit]


class MongoVectorSearchProvider:
    provider_name = "mongodb_vector_search"

    def __init__(
        self, database: MongoDatabase, index_name: str = "document_chunk_vector_index"
    ) -> None:
        self._collection = database["document_chunks"]
        self._index_name = index_name

    async def search(self, query_vector: list[float], limit: int) -> list[RetrievalCandidate]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._index_name,
                    "path": "embedding.vector",
                    "queryVector": query_vector,
                    "numCandidates": max(limit * 10, 10),
                    "limit": limit,
                }
            },
            {"$set": {"score": {"$meta": "vectorSearchScore"}}},
        ]
        try:
            cursor = self._collection.aggregate(pipeline)
            documents = await cursor.to_list(length=limit)
        except Exception as exc:
            raise VectorProviderError("MongoDB vector search is unavailable") from exc
        candidates: list[RetrievalCandidate] = []
        for document in documents:
            candidates.append(
                RetrievalCandidate(
                    chunk=DocumentChunk.model_validate(document["chunk"]),
                    score=float(document.get("score", 0.0)),
                )
            )
        return candidates


class LocalFaissFallbackProvider:
    provider_name = "faiss"

    def __init__(self, index_path: Path) -> None:
        self._index_path = index_path

    async def rebuild(self, vectors: list[IndexedVector]) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"chunk": item.chunk.model_dump(mode="json"), "vector": item.vector} for item in vectors
        ]
        self._index_path.write_text(json.dumps(payload), encoding="utf-8")

    async def search(self, query_vector: list[float], limit: int) -> list[RetrievalCandidate]:
        if not self._index_path.exists():
            raise VectorProviderError("FAISS fallback index has not been built")
        payload = json.loads(self._index_path.read_text(encoding="utf-8"))
        vectors = [
            IndexedVector(
                chunk=DocumentChunk.model_validate(item["chunk"]),
                vector=[float(value) for value in item["vector"]],
            )
            for item in payload
        ]
        ranked = [
            RetrievalCandidate(
                chunk=item.chunk, score=_cosine_similarity(query_vector, item.vector)
            )
            for item in vectors
        ]
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:limit]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise VectorProviderError("Vector dimension mismatch")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
