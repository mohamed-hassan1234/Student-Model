# Phase 3 Plan

## Objective

Implement controlled, reproducible, local-first LoRA training, evaluation, and model-candidate management for Technology Student v0.1. Phase 3 permits explicit manual training commands and metadata registration, but it must not automatically download models, train during startup/tests/CI, deploy, promote, replace, or publish model weights.

## Entry Gate

- Phase 0-2 audit report: `docs/audits/PHASE_0_2_AUDIT_REPORT.md`
- Decision: GO for Phase 3 development after human review; NO-GO for production/shared deployment until real authorization exists.
- Current worktree before Phase 3 implementation: clean.

## Milestones

1. Extend schemas and repositories for base-model manifests, hardware reports, dataset-entry reports, split manifests, training runs, artifacts, evaluations, comparisons, recommendations, approvals, rollback metadata, and adapter-loading checks.
2. Implement deterministic Phase 3 services for base-model validation, hardware inspection, dataset gate, split creation, baseline/evaluation records, mock smoke training, checkpoint/resume validation, artifact hashing, regression detection, deployment recommendation, and human approval.
3. Add versioned API endpoints under `/api/v1/technology/training` with administrative placeholders on all mutation or expensive operations.
4. Add frontend administrative pages for hardware assessment, base models, training datasets, training runs, and Phase 3 model candidates.
5. Add manual CLI commands for hardware inspection, manifest validation, dataset validation, split generation, baseline evaluation, resource estimation, smoke training, LoRA training stub, resume validation, adapter evaluation, comparison, candidate registration, recommendation, and experiment archival.
6. Update MongoDB indexes, validators, schema-version records, architecture/security/model/training/evaluation/API documentation, AGENTS/README/status, and move the completed audit plan to completed.
7. Run backend, frontend, training-specific, and repository guardrail validation.

## Files Affected

- `services/api/src/devmind_api/technology/learning_models.py`
- `services/api/src/devmind_api/technology/learning_repositories.py`
- `services/api/src/devmind_api/technology/learning_services.py`
- `services/api/src/devmind_api/routes/learning.py`
- `services/api/src/devmind_api/routes/training.py`
- `services/api/src/devmind_api/main.py`
- `scripts/training_cli.py`
- `infra/mongodb/indexes/system_indexes.json`
- `infra/mongodb/validators/system_validators.json`
- `infra/mongodb/schema_versions/phase_3.json`
- `apps/web/src/api/client.ts`
- `apps/web/src/App.tsx`
- `apps/web/src/components/*`
- `services/api/tests/*`
- `apps/web/src/App.test.tsx`
- `docs/training/*`
- `docs/evaluation/*`
- `docs/models/*`
- `docs/security/MODEL_TRAINING_SECURITY.md`
- `docs/api/PHASE_3_API.md`
- `docs/status/PROJECT_STATUS.md`

## Acceptance Criteria

- Base-model manifests refuse unresolved licenses, missing pinned revisions, unapproved remote code, and missing human approval.
- Hardware inspection reports realistic local limitations without claiming full training is practical.
- Dataset validation accepts only approved immutable dataset versions with approved, non-evaluation, non-secret, training-permitted records.
- Split manifests are reproducible and prevent duplicate/near-duplicate group leakage across train/validation/test.
- Baseline evaluation can be recorded honestly as unavailable when no approved local/remote inference host exists.
- Smoke training uses only mock/tiny local fixtures, writes hashed adapter/checkpoint/metrics artifacts outside Git, and records MongoDB metadata.
- LoRA training is exposed only as an explicit manual command and API job record; tests do not download models or require GPU.
- Candidate evaluation, regression detection, recommendation, and manual approval records are auditable and do not promote production models.
- Frontend exposes Phase 3 administrative views without implying a candidate is production.
- Tests and validation pass.

## Validation Commands

- `uv lock --check`: passed.
- `npm ci`: passed, 0 vulnerabilities.
- `npm audit --json`: passed, 0 vulnerabilities.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed.
- `uv run pytest`: passed, 50 passed and 1 guarded MongoDB integration test skipped.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed, 11 tests.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- Prohibited Docker/container scan: passed, no matches.
- Prohibited relational database scan: passed, no implementation matches.
- Secret-pattern scan: passed, no matches.
- Large/generated artifact scan: passed, no tracked generated/model artifacts.

## Phase 3 Result

Implemented and validated on Windows 11 with Python 3.12.13. Hardware detector reported approximately 15.72 GB RAM, no CUDA GPU, 33.38 GB free disk, and `cpu_only_smoke_test` as the recommended mode. First real Technology Student training run is NO-GO on this machine until an approved base-model manifest, approved dataset version, local model assets, optional training dependencies, and GPU/approved training host are available.

## Security Considerations

- Administrative placeholder headers are still not production authorization.
- No model download, training, or deployment runs automatically.
- Artifact paths are generated under ignored storage directories and must not overwrite existing artifacts silently.
- Base models requiring `trust_remote_code` are rejected unless explicitly approved in the manifest.
- Safetensors is preferred for real adapters; smoke artifacts are clearly marked as mock outputs.
- Pickle-based unsafe artifact loading is not implemented.

## Dependencies

- Existing Phase 2 dataset, evaluation, training-config, and model-candidate foundations.
- Optional real training packages are configured as a separate dependency group and are not required for normal app tests or CI.
- Real training requires a human-approved base-model manifest, approved immutable dataset version, local model assets, and sufficient hardware.

## Risks

- Real training may be impractical on the local machine.
- Placeholder admin authorization is not adequate for shared deployments.
- Optional training dependencies may be platform-sensitive.
- Smoke training validates control flow only, not model quality.

## Decisions

- Phase 3 adds controlled manual LoRA/QLoRA preparation and mock smoke training only.
- MongoDB stores metadata and artifact paths/hashes, not large model weights.
- Production model configuration is never changed by Phase 3 commands.

## Out Of Scope

Phase 4, final router, DevMind Teacher AI, multiple specialist models, automatic model download, automatic training, automatic deployment, model promotion, paid APIs, Docker, relational databases, and unrestricted crawling.
