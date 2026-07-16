# Source Registry

Technology Student v0.1 uses an allowlist source registry. A source must record identity, original reference, domain, content type, curriculum topic, trust level, author or organization, license metadata, retrieval/training permissions, human approval, checksums, status, ingestion status, and timestamps.

Sources cannot be ingested unless license review, retrieval permission, and human approval permit ingestion. Unsupported topics are rejected.

Statuses: `pending_review`, `approved`, `rejected`, `active`, `inactive`, `blocked`.
