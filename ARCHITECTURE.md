# DevMind AI Architecture

DevMind AI is organized as local-first processes coordinated through explicit service boundaries.

- `apps/web`: React status UI for Phase 0.
- `services/api`: FastAPI API with versioned routes, configuration validation, structured logging, request correlation IDs, central exception handling, and MongoDB readiness checks.
- `services/worker`: inactive-by-default MongoDB job worker foundation.
- `services/model_gateway`: provider contracts plus deterministic mock provider for Phase 0.
- `infra/mongodb`: idempotent bootstrap, indexes, validators, and schema-version records.
- `storage`: ignored local runtime storage for future uploads and GridFS-adjacent temporary files.

Deeper documentation:

- System architecture: `docs/architecture/SYSTEM_ARCHITECTURE.md`
- MongoDB architecture: `docs/database/MONGODB_ARCHITECTURE.md`
- Security boundaries: `docs/security/SECURITY.md`
- Source policy: `docs/data-governance/SOURCE_POLICY.md`
- Phase 0 plan: `docs/plans/active/PHASE_0_PLAN.md`

No Docker, relational database, paid provider, model download, training, crawling, final router, or final DevMind Teacher AI is part of Phase 0.
