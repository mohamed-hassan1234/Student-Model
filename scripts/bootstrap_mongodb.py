import asyncio
from collections.abc import Mapping
from typing import Any

from pymongo import ASCENDING, AsyncMongoClient

from devmind_api.config import Settings
from devmind_shared.time import utc_now

SYSTEM_SCHEMA_VERSION = 1
PHASE_1_SCHEMA_VERSION = 1
PHASE_2_SCHEMA_VERSION = 1
PHASE_3_SCHEMA_VERSION = 1
PHASE_4_SCHEMA_VERSION = 1

PHASE_2_COLLECTIONS = {
    "curricula": [("student_id", ASCENDING), ("version", ASCENDING)],
    "curriculum_topics": [("domain", ASCENDING), ("topic", ASCENDING), ("subtopic", ASCENDING)],
    "learning_cycles": [("status", ASCENDING), ("created_at", ASCENDING)],
    "knowledge_gaps": [("status", ASCENDING), ("severity", ASCENDING)],
    "generated_questions": [("topic", ASCENDING), ("content_hash", ASCENDING)],
    "candidate_answers": [("question_id", ASCENDING), ("verification_status", ASCENDING)],
    "verification_runs": [("candidate_id", ASCENDING), ("created_at", ASCENDING)],
    "verification_signals": [("candidate_id", ASCENDING), ("name", ASCENDING)],
    "human_reviews": [("status", ASCENDING), ("created_at", ASCENDING)],
    "reviewer_actions": [("review_id", ASCENDING), ("created_at", ASCENDING)],
    "dataset_candidates": [("status", ASCENDING), ("dataset_type", ASCENDING)],
    "dataset_versions": [("dataset_type", ASCENDING), ("creation_timestamp", ASCENDING)],
    "dataset_records": [("dataset_candidate_id", ASCENDING), ("content_hash", ASCENDING)],
    "evaluation_sets": [("version", ASCENDING)],
    "evaluation_records": [("category", ASCENDING), ("content_hash", ASCENDING)],
    "training_configs": [("dataset_version", ASCENDING), ("training_method", ASCENDING)],
    "training_runs": [("status", ASCENDING), ("created_at", ASCENDING)],
    "model_candidates": [("approval_state", ASCENDING), ("dataset_version", ASCENDING)],
    "model_evaluations": [("candidate_id", ASCENDING), ("created_at", ASCENDING)],
    "deployment_recommendations": [("candidate_id", ASCENDING)],
    "rollback_records": [("candidate_id", ASCENDING), ("created_at", ASCENDING)],
}

PHASE_3_COLLECTIONS = {
    "base_model_manifests": [("approval_status", ASCENDING), ("updated_at", ASCENDING)],
    "hardware_capability_reports": [("created_at", ASCENDING)],
    "training_dataset_validation_reports": [
        ("dataset_version_id", ASCENDING),
        ("created_at", ASCENDING),
    ],
    "dataset_split_manifests": [("dataset_version_id", ASCENDING), ("seed", ASCENDING)],
    "training_artifacts": [("training_run_id", ASCENDING), ("artifact_type", ASCENDING)],
    "candidate_comparisons": [("candidate_id", ASCENDING), ("created_at", ASCENDING)],
    "model_approvals": [("candidate_id", ASCENDING), ("created_at", ASCENDING)],
    "adapter_load_checks": [("candidate_id", ASCENDING), ("checked_at", ASCENDING)],
}

PHASE_4_COLLECTIONS = {
    "users": [("active", ASCENDING), ("created_at", ASCENDING)],
    "roles": [("role", ASCENDING)],
    "permissions": [("permission", ASCENDING)],
    "role_permissions": [("role", ASCENDING), ("permission", ASCENDING)],
    "user_roles": [("user_id", ASCENDING), ("role", ASCENDING)],
    "auth_sessions": [("user_id", ASCENDING), ("revoked", ASCENDING)],
    "refresh_token_families": [("user_id", ASCENDING), ("revoked", ASCENDING)],
    "login_attempts": [("normalized_email", ASCENDING), ("created_at", -1)],
    "password_reset_events": [("user_id", ASCENDING), ("created_at", -1)],
    "security_events": [("severity", ASCENDING), ("created_at", -1)],
    "governance_policies": [("policy_id", ASCENDING)],
    "approval_workflows": [("status", ASCENDING), ("created_at", -1)],
    "approval_requests": [("candidate_id", ASCENDING), ("status", ASCENDING)],
    "approval_decisions": [("approval_request_id", ASCENDING), ("decision_type", ASCENDING)],
    "staging_requests": [("candidate_id", ASCENDING), ("status", ASCENDING)],
    "staging_events": [("staging_request_id", ASCENDING), ("created_at", ASCENDING)],
    "production_model_assignments": [("environment", ASCENDING), ("active", ASCENDING)],
}


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
    await database["sources"].create_index(
        [("source_id", ASCENDING)], unique=True, name="uniq_source_id"
    )
    await database["sources"].create_index([("source_status", ASCENDING)], name="source_status")
    await database["sources"].create_index(
        [("technology_topic", ASCENDING)], name="technology_topic"
    )
    await database["sources"].create_index(
        [("content_checksum", ASCENDING)], name="content_checksum"
    )
    await database["source_reviews"].create_index(
        [("source_id", ASCENDING), ("created_at", ASCENDING)], name="source_review_history"
    )
    await database["documents"].create_index([("source_id", ASCENDING)], name="document_source")
    await database["documents"].create_index(
        [("content_hash", ASCENDING)], name="document_content_hash"
    )
    await database["document_versions"].create_index(
        [("document_id", ASCENDING), ("created_at", ASCENDING)], name="document_version_history"
    )
    await database["document_chunks"].create_index(
        [("source_id", ASCENDING), ("document_id", ASCENDING)], name="chunk_source_document"
    )
    await database["document_chunks"].create_index(
        [("content_hash", ASCENDING)], unique=True, name="uniq_chunk_content_hash"
    )
    await database["document_chunks"].create_index(
        [("technology_topic", ASCENDING)], name="chunk_topic"
    )
    await database["document_chunks"].create_index([("chunk.text", "text")], name="chunk_text")
    await database["ingestion_jobs"].create_index(
        [("state", ASCENDING), ("created_at", ASCENDING)], name="ingestion_state_created"
    )
    await database["ingestion_jobs"].create_index(
        [("lease_until", ASCENDING)], name="ingestion_lease_until"
    )
    await database["ingestion_events"].create_index(
        [("source_id", ASCENDING), ("created_at", ASCENDING)], name="ingestion_event_source"
    )
    await database["conversations"].create_index(
        [("created_at", ASCENDING)], name="conversation_created"
    )
    await database["messages"].create_index(
        [("conversation_id", ASCENDING), ("created_at", ASCENDING)], name="message_conversation"
    )
    await database["retrieval_events"].create_index(
        [("created_at", ASCENDING)], name="retrieval_created"
    )
    await database["answer_evidence"].create_index(
        [("retrieval_event_id", ASCENDING)], name="answer_evidence_retrieval"
    )
    await database["vector_index_metadata"].create_index(
        [("provider", ASCENDING)], name="vector_provider"
    )
    await database["uploaded_source_files"].create_index(
        [("source_id", ASCENDING), ("upload_timestamp", ASCENDING)],
        name="uploaded_source_history",
    )
    await database["uploaded_source_files"].create_index(
        [("sha256_checksum", ASCENDING)],
        name="uploaded_source_checksum",
    )
    for collection_name, keys in PHASE_2_COLLECTIONS.items():
        await database[collection_name].create_index(keys, name=f"{collection_name}_primary")
    for collection_name, keys in PHASE_3_COLLECTIONS.items():
        await database[collection_name].create_index(keys, name=f"{collection_name}_primary")
    for collection_name, keys in PHASE_4_COLLECTIONS.items():
        await database[collection_name].create_index(keys, name=f"{collection_name}_primary")
    await database["curriculum_topics"].create_index(
        [("topic_id", ASCENDING)], unique=True, name="uniq_topic_id"
    )
    await database["generated_questions"].create_index(
        [("content_hash", ASCENDING)], name="question_content_hash"
    )
    await database["dataset_versions"].create_index(
        [("dataset_version_id", ASCENDING)], unique=True, name="uniq_dataset_version_id"
    )
    await database["dataset_records"].create_index(
        [("content_hash", ASCENDING)], name="dataset_record_content_hash"
    )
    await database["training_configs"].create_index(
        [("dataset_version_id", ASCENDING), ("training_method", ASCENDING)],
        name="phase3_training_configs_dataset_method",
    )
    await database["training_runs"].create_index(
        [("training_config_version", ASCENDING)], name="training_runs_config"
    )
    await database["model_candidates"].create_index(
        [("training_run_id", ASCENDING)], name="model_candidates_training_run"
    )
    await database["model_evaluations"].create_index(
        [("subject_id", ASCENDING), ("created_at", ASCENDING)],
        name="model_evaluations_subject",
    )
    await database["users"].create_index(
        [("normalized_email", ASCENDING)], unique=True, name="uniq_user_normalized_email"
    )
    await database["auth_sessions"].create_index(
        [("refresh_token_hash", ASCENDING)], unique=True, name="uniq_refresh_token_hash"
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
        "sources": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "source_id",
                    "name",
                    "source_status",
                    "technology_topic",
                    "created_at",
                ],
                "properties": {
                    "source_id": {"bsonType": "string"},
                    "name": {"bsonType": "string"},
                    "source_status": {"bsonType": "string"},
                    "technology_topic": {"bsonType": "string"},
                },
            }
        },
        "source_reviews": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["source_id", "decision", "created_at"],
            }
        },
        "documents": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["source_id", "title", "content_hash"],
            }
        },
        "document_versions": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["document_id", "source_id", "content_hash"],
            }
        },
        "document_chunks": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["source_id", "document_id", "chunk", "embedding"],
            }
        },
        "ingestion_jobs": {
            "$jsonSchema": {"bsonType": "object", "required": ["source_id", "state", "created_at"]}
        },
        "ingestion_events": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["source_id", "event_type", "created_at"],
            }
        },
        "conversations": {"$jsonSchema": {"bsonType": "object", "required": ["created_at"]}},
        "messages": {
            "$jsonSchema": {"bsonType": "object", "required": ["conversation_id", "created_at"]}
        },
        "retrieval_events": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["question", "evidence_status", "created_at"],
            }
        },
        "answer_evidence": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["retrieval_event_id", "source_id", "document_id"],
            }
        },
        "vector_index_metadata": {
            "$jsonSchema": {"bsonType": "object", "required": ["provider", "updated_at"]}
        },
        "uploaded_source_files": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "source_id",
                    "sanitized_filename",
                    "mime_type",
                    "file_size",
                    "sha256_checksum",
                    "gridfs_file_id",
                    "upload_timestamp",
                ],
            }
        },
    }
    for collection_name in PHASE_2_COLLECTIONS:
        validators[collection_name] = {"$jsonSchema": {"bsonType": "object", "required": ["_id"]}}
    for collection_name in PHASE_3_COLLECTIONS:
        validators[collection_name] = {"$jsonSchema": {"bsonType": "object", "required": ["_id"]}}
    for collection_name in PHASE_4_COLLECTIONS:
        validators[collection_name] = {"$jsonSchema": {"bsonType": "object", "required": ["_id"]}}
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
    await database["system_schema_versions"].update_one(
        {"component": "phase_1_technology_student"},
        {
            "$set": {
                "component": "phase_1_technology_student",
                "version": PHASE_1_SCHEMA_VERSION,
                "updated_at": utc_now(),
            }
        },
        upsert=True,
    )
    await database["system_schema_versions"].update_one(
        {"component": "phase_2_verified_dataset_builder"},
        {
            "$set": {
                "component": "phase_2_verified_dataset_builder",
                "version": PHASE_2_SCHEMA_VERSION,
                "updated_at": utc_now(),
            }
        },
        upsert=True,
    )
    await database["system_schema_versions"].update_one(
        {"component": "phase_3_controlled_lora_training"},
        {
            "$set": {
                "component": "phase_3_controlled_lora_training",
                "version": PHASE_3_SCHEMA_VERSION,
                "updated_at": utc_now(),
            }
        },
        upsert=True,
    )
    await database["system_schema_versions"].update_one(
        {"component": "phase_4_auth_governance_staging"},
        {
            "$set": {
                "component": "phase_4_auth_governance_staging",
                "version": PHASE_4_SCHEMA_VERSION,
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
