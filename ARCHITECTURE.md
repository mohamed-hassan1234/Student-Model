# DevMind AI Architecture

DevMind AI is organized as local-first processes coordinated through explicit service boundaries.

- `apps/web`: React UI for status, sources, Technology Student chat, and curriculum coverage.
- `services/api`: FastAPI API with versioned routes, configuration validation, structured logging, request correlation IDs, central exception handling, and MongoDB readiness checks.
- `services/worker`: inactive-by-default MongoDB job worker foundation with Phase 1 lease metadata.
- `services/model_gateway`: provider contracts plus mock and local HTTP provider foundations.
- `services/api/src/devmind_api/technology`: Phase 1 Technology Student source registry, ingestion, parsing, chunking, embeddings, retrieval, and cited RAG answer construction.
- `infra/mongodb`: idempotent bootstrap, indexes, validators, and schema-version records.
- `storage`: ignored local runtime storage for future uploads and GridFS-adjacent temporary files.

Deeper documentation:

- System architecture: `docs/architecture/SYSTEM_ARCHITECTURE.md`
- MongoDB architecture: `docs/database/MONGODB_ARCHITECTURE.md`
- Security boundaries: `docs/security/SECURITY.md`
- Source policy: `docs/data-governance/SOURCE_POLICY.md`
- Phase 1 plan: `docs/plans/active/PHASE_1_PLAN.md`

No Docker, relational database, paid provider, model download, fine-tuning, unrestricted crawling, final router, or final DevMind Teacher AI is part of Phase 1.
