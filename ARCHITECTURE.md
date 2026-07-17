# DevMind AI Architecture

DevMind AI is organized as local-first processes coordinated through explicit service boundaries.

- `apps/web`: React UI for status, sources, Technology Student chat, curriculum coverage, learning cycles, human review, dataset registry, Phase 3 hardware/base-model/training-run views, and model-candidate registry.
- `services/api`: FastAPI API with versioned routes, configuration validation, structured logging, request correlation IDs, central exception handling, and MongoDB readiness checks.
- `services/worker`: inactive-by-default MongoDB job worker foundation with Phase 1 lease metadata.
- `services/model_gateway`: provider contracts plus mock and local HTTP provider foundations.
- `services/api/src/devmind_api/technology`: Phase 1 Technology Student source registry, ingestion, parsing, chunking, embeddings, retrieval, and cited RAG answer construction.
- `services/api/src/devmind_api/technology/learning_*`: Phase 2 verified-learning and dataset-builder foundations with curriculum coverage, gap detection, bounded generation, verification, review, immutable dataset versions, export, training-prep validation, and deployment-gate metadata.
- `services/api/src/devmind_api/technology/training_*`: Phase 3 controlled training foundations with base-model manifests, hardware reports, dataset gates, splits, training runs, artifact hashes, evaluations, comparisons, recommendations, approvals, and adapter checks.
- `infra/mongodb`: idempotent bootstrap, indexes, validators, and schema-version records.
- `storage`: ignored local runtime storage for future uploads and GridFS-adjacent temporary files.

Deeper documentation:

- System architecture: `docs/architecture/SYSTEM_ARCHITECTURE.md`
- MongoDB architecture: `docs/database/MONGODB_ARCHITECTURE.md`
- Security boundaries: `docs/security/SECURITY.md`
- Source policy: `docs/data-governance/SOURCE_POLICY.md`
- Phase 3 plan: `docs/plans/active/PHASE_3_PLAN.md`
- Verified learning architecture: `docs/architecture/LEARNING_CYCLE_ARCHITECTURE.md`
- Dataset governance: `docs/data-governance/DATASET_GOVERNANCE.md`

No Docker, relational database, paid provider, automatic model download, automatic fine-tuning, unrestricted crawling, final router, or final DevMind Teacher AI is part of Phase 3.
