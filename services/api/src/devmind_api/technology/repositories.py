from collections.abc import Mapping
from typing import Any, cast

from devmind_api.db import MongoDatabase
from devmind_api.technology.models import (
    DocumentChunk,
    EmbeddedChunk,
    IngestionStatus,
    RagAnswer,
    RegisteredSource,
    document_to_mongo,
)
from devmind_shared.time import utc_now


class TechnologyRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def create_source(self, source: RegisteredSource) -> RegisteredSource:
        document = document_to_mongo(source)
        document["_id"] = source.source_id
        await self._database["sources"].insert_one(document)
        await self.record_audit_event(
            "source_registered",
            {"source_id": source.source_id, "topic": source.technology_topic},
        )
        return source

    async def list_sources(
        self,
        *,
        status: str | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RegisteredSource]:
        query: dict[str, Any] = {}
        if status:
            query["source_status"] = status
        if topic:
            query["technology_topic"] = topic
        cursor = (
            self._database["sources"].find(query).sort("created_at", -1).skip(offset).limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [RegisteredSource.model_validate(document) for document in documents]

    async def get_source(self, source_id: str) -> RegisteredSource | None:
        document = await self._database["sources"].find_one({"_id": source_id})
        return RegisteredSource.model_validate(document) if document else None

    async def update_source(
        self, source_id: str, updates: Mapping[str, Any]
    ) -> RegisteredSource | None:
        update_document = dict(updates)
        update_document["updated_at"] = utc_now()
        await self._database["sources"].update_one({"_id": source_id}, {"$set": update_document})
        return await self.get_source(source_id)

    async def record_source_review(
        self,
        source_id: str,
        reviewer: str,
        decision: str,
        notes: str | None = None,
    ) -> None:
        now = utc_now()
        await self._database["source_reviews"].insert_one(
            {
                "source_id": source_id,
                "reviewer": reviewer,
                "decision": decision,
                "notes": notes,
                "created_at": now,
            }
        )
        await self.record_audit_event(
            "source_reviewed", {"source_id": source_id, "decision": decision}
        )

    async def create_ingestion_job(self, source_id: str, created_by: str) -> str:
        now = utc_now()
        job_id = f"ing_{source_id}_{int(now.timestamp())}"
        await self._database["ingestion_jobs"].insert_one(
            {
                "_id": job_id,
                "source_id": source_id,
                "state": "queued",
                "attempts": 0,
                "max_attempts": 3,
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
                "lease_until": None,
                "safe_error_summary": None,
            }
        )
        await self.record_ingestion_event(job_id, source_id, "queued", "Ingestion queued")
        return job_id

    async def record_upload_metadata(
        self,
        *,
        source_id: str,
        original_filename: str,
        sanitized_filename: str,
        mime_type: str,
        file_size: int,
        checksum: str,
        gridfs_file_id: str,
        permission_metadata: Mapping[str, Any],
        license_metadata: Mapping[str, Any],
    ) -> None:
        await self._database["uploaded_source_files"].insert_one(
            {
                "source_id": source_id,
                "original_filename": original_filename,
                "sanitized_filename": sanitized_filename,
                "mime_type": mime_type,
                "file_size": file_size,
                "sha256_checksum": checksum,
                "upload_timestamp": utc_now(),
                "permission_metadata": dict(permission_metadata),
                "license_metadata": dict(license_metadata),
                "gridfs_file_id": gridfs_file_id,
                "parsing_status": "registered",
            }
        )

    async def get_ingestion_job(self, job_id: str) -> Mapping[str, Any] | None:
        document = await self._database["ingestion_jobs"].find_one({"_id": job_id})
        return cast(Mapping[str, Any] | None, document)

    async def list_ingestion_jobs(
        self, limit: int = 50, offset: int = 0
    ) -> list[Mapping[str, Any]]:
        cursor = (
            self._database["ingestion_jobs"]
            .find({})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return cast(list[Mapping[str, Any]], await cursor.to_list(length=limit))

    async def update_ingestion_job(self, job_id: str, updates: Mapping[str, Any]) -> None:
        update_document = dict(updates)
        update_document["updated_at"] = utc_now()
        await self._database["ingestion_jobs"].update_one(
            {"_id": job_id}, {"$set": update_document}
        )

    async def record_ingestion_event(
        self,
        job_id: str,
        source_id: str,
        event_type: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        await self._database["ingestion_events"].insert_one(
            {
                "job_id": job_id,
                "source_id": source_id,
                "event_type": event_type,
                "message": message,
                "metadata": dict(metadata or {}),
                "created_at": utc_now(),
            }
        )

    async def create_document_with_chunks(
        self,
        *,
        source: RegisteredSource,
        document_id: str,
        document_version_id: str,
        title: str,
        content_hash: str,
        chunks: list[DocumentChunk],
        embeddings: list[EmbeddedChunk],
        extraction_warnings: list[str],
    ) -> None:
        now = utc_now()
        await self._database["documents"].update_one(
            {"_id": document_id},
            {
                "$set": {
                    "_id": document_id,
                    "source_id": source.source_id,
                    "title": title,
                    "current_version_id": document_version_id,
                    "content_hash": content_hash,
                    "ingestion_status": IngestionStatus.COMPLETED.value,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        await self._database["document_versions"].update_one(
            {"_id": document_version_id},
            {
                "$set": {
                    "_id": document_version_id,
                    "document_id": document_id,
                    "source_id": source.source_id,
                    "content_hash": content_hash,
                    "extraction_warnings": extraction_warnings,
                    "created_at": now,
                }
            },
            upsert=True,
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            document = {
                "_id": chunk.chunk_id,
                "chunk": chunk.model_dump(mode="python"),
                "embedding": embedding.model_dump(mode="python"),
                "source_id": source.source_id,
                "document_id": document_id,
                "content_hash": chunk.content_hash,
                "technology_topic": source.technology_topic,
                "created_at": now,
            }
            await self._database["document_chunks"].update_one(
                {"_id": chunk.chunk_id},
                {"$set": document},
                upsert=True,
            )
        await self.update_source(
            source.source_id,
            {
                "content_checksum": content_hash,
                "ingestion_status": IngestionStatus.COMPLETED.value,
            },
        )

    async def find_chunks_by_topic(
        self, topic: str | None, limit: int = 50
    ) -> list[Mapping[str, Any]]:
        query: dict[str, Any] = {}
        if topic:
            query["technology_topic"] = topic
        cursor = self._database["document_chunks"].find(query).limit(limit)
        return cast(list[Mapping[str, Any]], await cursor.to_list(length=limit))

    async def record_retrieval_event(
        self,
        *,
        question: str,
        topic: str | None,
        answer: RagAnswer,
        chunk_ids: list[str],
    ) -> str:
        now = utc_now()
        event_id = f"ret_{int(now.timestamp() * 1000)}"
        await self._database["retrieval_events"].insert_one(
            {
                "_id": event_id,
                "question": question,
                "topic": topic,
                "evidence_status": answer.evidence_status.value,
                "confidence": answer.confidence,
                "chunk_ids": chunk_ids,
                "created_at": now,
            }
        )
        for citation in answer.sources:
            await self._database["answer_evidence"].insert_one(
                {
                    "retrieval_event_id": event_id,
                    **citation.model_dump(mode="python"),
                    "created_at": now,
                }
            )
        await self.record_audit_event(
            "retrieval_completed",
            {"retrieval_event_id": event_id, "evidence_status": answer.evidence_status.value},
        )
        return event_id

    async def record_audit_event(self, event_type: str, metadata: Mapping[str, Any]) -> None:
        await self._database["system_audit_events"].insert_one(
            {
                "event_type": event_type,
                "metadata": dict(metadata),
                "created_at": utc_now(),
            }
        )

    async def update_vector_index_metadata(
        self, provider: str, metadata: Mapping[str, Any]
    ) -> None:
        await self._database["vector_index_metadata"].update_one(
            {"_id": provider},
            {"$set": {"provider": provider, "metadata": dict(metadata), "updated_at": utc_now()}},
            upsert=True,
        )
