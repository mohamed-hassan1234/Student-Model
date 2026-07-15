from typing import Any

from devmind_worker.jobs import JobRepository, JobState


class InsertResult:
    def __init__(self, inserted_id: str) -> None:
        self.inserted_id = inserted_id


class FakeJobsCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []
        self.next_id = 1

    async def insert_one(self, document: dict[str, Any]) -> InsertResult:
        stored = dict(document)
        stored["_id"] = f"job-{self.next_id}"
        self.next_id += 1
        self.documents.append(stored)
        return InsertResult(stored["_id"])

    async def find_one_and_update(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        sort: list[tuple[str, int]],
        return_document: Any,
    ) -> dict[str, Any] | None:
        del query, sort, return_document
        for document in self.documents:
            if document["state"] == JobState.QUEUED.value:
                document.update(update["$set"])
                document["attempts"] += update["$inc"]["attempts"]
                return document
        return None

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        for document in self.documents:
            if document["_id"] == query["_id"]:
                document.update(update["$set"])


class FakeDatabase:
    def __init__(self) -> None:
        self.jobs = FakeJobsCollection()

    def __getitem__(self, name: str) -> FakeJobsCollection:
        assert name == "system_jobs"
        return self.jobs


async def test_job_state_transitions() -> None:
    database = FakeDatabase()
    repository = JobRepository(database)  # type: ignore[arg-type]

    job_id = await repository.enqueue("noop", {"value": 1})
    lease = await repository.claim_next("worker-1")
    assert lease is not None
    assert lease.job_id == job_id
    assert lease.state is JobState.RUNNING
    assert lease.attempts == 1

    await repository.complete(job_id)

    assert database.jobs.documents[0]["state"] == JobState.COMPLETED.value
