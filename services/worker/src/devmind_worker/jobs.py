from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pymongo import ReturnDocument

from devmind_api.db import MongoDatabase
from devmind_shared.time import utc_now


class JobState(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class JobLease:
    job_id: str
    state: JobState
    attempts: int
    max_attempts: int
    payload: dict[str, Any]


class JobRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._collection = database["system_jobs"]

    async def enqueue(self, job_type: str, payload: dict[str, Any] | None = None) -> str:
        now = utc_now()
        document = {
            "job_type": job_type,
            "state": JobState.QUEUED.value,
            "payload": payload or {},
            "attempts": 0,
            "max_attempts": 3,
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "heartbeat_at": None,
            "lease_until": None,
            "error_category": None,
            "last_error": None,
        }
        result = await self._collection.insert_one(document)
        return str(result.inserted_id)

    async def claim_next(self, worker_id: str, lease_seconds: int = 60) -> JobLease | None:
        now = utc_now()
        lease_until = now.timestamp() + lease_seconds
        document = await self._collection.find_one_and_update(
            {
                "state": JobState.QUEUED.value,
                "attempts": {"$lt": 3},
                "$or": [{"lease_until": None}, {"lease_until": {"$lte": now.timestamp()}}],
            },
            {
                "$set": {
                    "state": JobState.CLAIMED.value,
                    "worker_id": worker_id,
                    "lease_until": lease_until,
                    "updated_at": now,
                },
                "$inc": {"attempts": 1},
            },
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if document is None:
            return None
        return JobLease(
            job_id=str(document["_id"]),
            state=JobState(document["state"]),
            attempts=int(document["attempts"]),
            max_attempts=int(document.get("max_attempts", 3)),
            payload=dict(document.get("payload") or {}),
        )

    async def mark_running(self, job_id: str, worker_id: str) -> None:
        now = utc_now()
        await self._collection.update_one(
            {"_id": job_id, "worker_id": worker_id, "state": JobState.CLAIMED.value},
            {"$set": {"state": JobState.RUNNING.value, "started_at": now, "updated_at": now}},
        )

    async def heartbeat(self, job_id: str, worker_id: str, lease_seconds: int = 60) -> None:
        now = utc_now()
        await self._collection.update_one(
            {"_id": job_id, "worker_id": worker_id, "state": JobState.RUNNING.value},
            {
                "$set": {
                    "heartbeat_at": now,
                    "lease_until": now.timestamp() + lease_seconds,
                    "updated_at": now,
                }
            },
        )

    async def complete(self, job_id: str) -> None:
        await self._transition(job_id, JobState.COMPLETED)

    async def fail(self, job_id: str, error_message: str, error_category: str = "unknown") -> None:
        await self._transition(
            job_id,
            JobState.FAILED,
            safe_error=error_message[:500],
            error_category=error_category[:120],
        )

    async def cancel(self, job_id: str) -> None:
        await self._transition(job_id, JobState.CANCELLED)

    async def _transition(
        self,
        job_id: str,
        state: JobState,
        safe_error: str | None = None,
        error_category: str | None = None,
    ) -> None:
        now = utc_now()
        await self._collection.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "state": state.value,
                    "updated_at": now,
                    "finished_at": now,
                    "completed_at": now,
                    "last_error": safe_error,
                    "error_category": error_category,
                    "lease_until": None,
                }
            },
        )
