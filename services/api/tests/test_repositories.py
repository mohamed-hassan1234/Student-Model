from fakes import FakeMongoDatabase

from devmind_api.repositories import SystemRepository


async def test_system_repository_uses_system_collections() -> None:
    database = FakeMongoDatabase()
    repository = SystemRepository(database)

    inserted_id = await repository.record_audit_event({"event_type": "test"})

    assert inserted_id == "fake-id"
    assert database.collections["system_audit_events"].documents[0]["event_type"] == "test"
