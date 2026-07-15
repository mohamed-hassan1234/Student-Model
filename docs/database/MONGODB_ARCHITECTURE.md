# MongoDB Architecture

## Why MongoDB

DevMind AI needs flexible documents for source provenance, audit events, job state, future metadata, and future model/tool records. MongoDB supports local Community Server development, Atlas via environment URI, async Python access through PyMongo, indexes, validators, and GridFS.

## Naming

Local database default: `devmind_local`. Test database default: `devmind_test`. Test database names must be explicit and safe. Collection names use lowercase snake case, with infrastructure collections prefixed by `system_`.

## Document IDs

MongoDB ObjectIds are acceptable by default. Application-created IDs may be added later where deterministic external references are required.

## UTC Timestamp Policy

All persisted timestamps must be timezone-aware UTC values at the application boundary and stored as MongoDB date values.

## Index Strategy

Indexes are declared in `infra/mongodb/indexes` and applied idempotently by `scripts/bootstrap_mongodb.py`. Phase 0 indexes support schema-version lookup, audit review by event/time, and job queue claiming.

## Unique Index Strategy

Unique indexes should be used for true invariants only. Phase 0 uses a unique index on `system_schema_versions.component`.

## Text Index Considerations

Text indexes are not created in Phase 0. Future search requirements must document language, scoring, source policy, and retention implications.

## Vector Field Planning

Vector fields are not created in Phase 0. Future vector search must be documented with provider, dimensionality, storage cost, provenance, and fallback strategy. pgvector is prohibited.

## GridFS Planning

Durable file storage should use MongoDB GridFS where appropriate. Phase 0 defines a `FileStore` and `GridFsFileStore` boundary but does not implement upload workflows.

## Schema Validation Strategy

Infrastructure collection validators are applied with MongoDB JSON schema through the bootstrap script. Validation should be moderate enough to support safe evolution while rejecting malformed infrastructure records.

## Schema Version Strategy

`system_schema_versions` records infrastructure component versions. Bootstrap operations must be idempotent.

## Bootstrap Scripts

`uv run python scripts/bootstrap_mongodb.py` checks connectivity, creates or updates validators, creates indexes, and records Phase 0 schema version.

## Backup Expectations

Local developers are responsible for local backups if they store important data. Production deployment planning must define backup cadence, restore tests, and retention before real data use.

## Local Configuration

Use MongoDB Community Server locally with `MONGODB_URI=mongodb://127.0.0.1:27017` unless a different local URI is explicitly configured.

## Atlas Configuration

MongoDB Atlas may be used through `MONGODB_URI`. Credentials must stay in local environment variables or a secrets manager, never in source control.

## Test Database Naming

Real MongoDB integration tests require `MONGODB_TEST_URI` and a database name starting with `devmind_test`. They are marked `mongodb` and skipped when no URI is configured.

## Data Retention

Retention policies are not implemented in Phase 0. Future dataset, audit, upload, and job-retention rules must be documented before production data collection.

## Audit Event Design

`system_audit_events` is the foundation for security and governance events. Events must avoid secrets and should include event type, timestamp, actor where available, and safe metadata.
