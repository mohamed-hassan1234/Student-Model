import asyncio
from collections.abc import Mapping
from typing import Any

from pymongo import ASCENDING, AsyncMongoClient

from devmind_api.config import Settings
from devmind_shared.time import utc_now

SYSTEM_SCHEMA_VERSION = 1


async def create_indexes(database: Any) -> None:
    await database["system_schema_versions"].create_index(
        [("component", ASCENDING)],
        unique=True,
        name="uniq_component",
    )
    await database["system_audit_events"].create_index(
        [("created_at", ASCENDING)],
        name="created_at",
    )
    await database["system_audit_events"].create_index(
        [("event_type", ASCENDING), ("created_at", ASCENDING)],
        name="event_type_created_at",
    )
    await database["system_jobs"].create_index(
        [("state", ASCENDING), ("created_at", ASCENDING)],
        name="state_created_at",
    )
    await database["system_jobs"].create_index(
        [("lease_until", ASCENDING)],
        name="lease_until",
    )


async def create_validators(database: Any) -> None:
    validators: dict[str, Mapping[str, Any]] = {
        "system_schema_versions": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["component", "version", "updated_at"],
                "properties": {
                    "component": {"bsonType": "string"},
                    "version": {"bsonType": "int"},
                    "updated_at": {"bsonType": "date"},
                },
            }
        },
        "system_audit_events": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["event_type", "created_at"],
                "properties": {
                    "event_type": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "metadata": {"bsonType": "object"},
                },
            }
        },
        "system_jobs": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["job_type", "state", "attempts", "created_at", "updated_at"],
                "properties": {
                    "job_type": {"bsonType": "string"},
                    "state": {
                        "enum": ["queued", "running", "completed", "failed", "cancelled"],
                    },
                    "attempts": {"bsonType": "int"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "payload": {"bsonType": "object"},
                },
            }
        },
    }
    existing = await database.list_collection_names()
    for collection_name, validator in validators.items():
        if collection_name not in existing:
            await database.create_collection(collection_name, validator=validator)
        else:
            await database.command(
                {
                    "collMod": collection_name,
                    "validator": validator,
                    "validationLevel": "moderate",
                }
            )


async def record_schema_version(database: Any) -> None:
    await database["system_schema_versions"].update_one(
        {"component": "phase_0_foundation"},
        {
            "$set": {
                "component": "phase_0_foundation",
                "version": SYSTEM_SCHEMA_VERSION,
                "updated_at": utc_now(),
            }
        },
        upsert=True,
    )


async def bootstrap() -> None:
    settings = Settings()
    client: AsyncMongoClient[Any] = AsyncMongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_connect_timeout_ms,
        connectTimeoutMS=settings.mongodb_connect_timeout_ms,
    )
    try:
        database = client[settings.mongodb_database]
        await client.admin.command("ping")
        await create_validators(database)
        await create_indexes(database)
        await record_schema_version(database)
    finally:
        await client.close()


def main() -> int:
    asyncio.run(bootstrap())
    print("MongoDB bootstrap completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
