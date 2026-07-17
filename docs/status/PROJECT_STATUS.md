# Project Status

## Phase 0 Status

Complete and audited. Phase 0 provides the repository foundation, Python 3.12 configuration, FastAPI health/readiness endpoints, environment-based configuration, MongoDB lifecycle/readiness ping, structured logging, correlation IDs, central exception handling, React status UI, mock model provider, MongoDB-backed worker foundation, local scripts, CI, and no Docker or relational database dependency.

## Phase 1 Status

Complete and audited. Phase 1 provides Technology Student approved-source registration, policy validation, secure ingestion, parsing, sanitization, normalization, duplicate-aware chunking, embeddings, MongoDB storage, GridFS upload metadata, retrieval, local/mock provider generation, citations, insufficient-evidence behavior, prompt-injection isolation, SSRF/file validation, and audit events.

## Phase 2 Status

Complete and audited. Phase 2 provides curriculum coverage, knowledge-gap detection, bounded learning cycles, generated-question records, candidate-answer records, teacher provenance, verification signals, risk scoring, human review, review audit trail, immutable dataset versions, reproducible exports with sidecar manifests, evaluation-set separation, training-config validation, model-candidate registry, and non-deploying recommendations.

## Phase 3 Status

Implemented and under validation. Phase 3 provides base-model manifest registration/validation, hardware capability inspection, approved dataset entry gate, reproducible split manifests, manual training configuration validation, explicit smoke-training execution, training-run and artifact metadata, baseline unavailable records, candidate mock evaluation records, regression detection, comparison reports, model-candidate registration, advisory deployment recommendations, manual approval actions, adapter load checks, API endpoints, frontend administration pages, docs, and tests. Phase 3 does not automatically download models, start real training, deploy, promote, or change production model settings.

## Audit Status

Phase 0-2 audit completed. Audit plan moved to `docs/plans/completed/PHASE_0_2_AUDIT_PLAN.md`. Active plan: `docs/plans/active/PHASE_3_PLAN.md`. Audit report: `docs/audits/PHASE_0_2_AUDIT_REPORT.md`.

## Validation Results

Final audit validation on 2026-07-17:

- `uv lock --check`: passed.
- `uv sync --locked`: passed.
- `npm ci`: passed, 0 vulnerabilities.
- `npm audit --json`: passed, 0 vulnerabilities.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed.
- `uv run pytest`: passed, 43 passed and 1 skipped guarded MongoDB integration test.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- PowerShell syntax parse checks for `scripts/validate.ps1`, `scripts/dev.ps1`, and `scripts/stop.ps1`: passed.
- Explicit no-Docker scan: passed.
- Explicit no-relational implementation scan: passed.
- Python 3.12 scan: passed; the only non-3.12 version-style hit was an npm package version, not a Python runtime reference.
- Secret-pattern scan: reviewed; hits are placeholders, test redaction fixtures, policy text, or variable names, not committed secrets.
- Tracked generated-artifact scan: passed.

Environment limitations:

- `sh` is not installed in this Windows environment, so POSIX shell syntax checks for `scripts/*.sh` were not executed here. Exact local command: `sh -n scripts/validate.sh scripts/dev.sh scripts/stop.sh`.
- Optional real MongoDB integration tests remained skipped because `MONGODB_TEST_URI` was not explicitly configured for a safe test database. The repository validation script did verify MongoDB connectivity for the configured local environment.

Phase 3 focused validation during implementation:

- `uv run pytest services/api/tests/test_training_phase3_service.py services/api/tests/test_training_phase3_api.py`: passed, 7 tests.
- `uv run mypy` focused on Phase 3 backend additions: passed.
- `npm --prefix apps/web run lint`: passed after Phase 3 frontend pages.
- `npm --prefix apps/web run typecheck`: passed after Phase 3 frontend pages.
- `npm --prefix apps/web run test:run`: passed, 11 tests.

Final Phase 3 validation on 2026-07-17:

- `uv lock --check`: passed.
- `npm ci`: passed, 0 vulnerabilities.
- `npm audit --json`: passed, 0 vulnerabilities.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed.
- `uv run pytest`: passed, 50 passed and 1 skipped guarded MongoDB integration test.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed, 11 tests.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- Explicit no-Docker scan: passed, no matches.
- Explicit no-relational implementation scan: passed, no matches.
- Explicit secret-pattern scan: passed, no matches.
- Tracked generated/model artifact scan: passed, no matches.
- Hardware capability detector: Windows 11, Python 3.12.13, Intel CPU, about 15.72 GB RAM, no CUDA GPU, 33.38 GB free disk, recommended mode `cpu_only_smoke_test`.

## Known Limitations

- Administrative authorization is a placeholder header and not production security.
- Teacher generation is deterministic mock output by default.
- Safe Code Runner is disabled and no arbitrary generated code is executed.
- Training configuration validation does not download models or start training.
- Real LoRA training requires optional local training dependencies and approved local model assets; this environment validated smoke training only.
- First real Technology Student LoRA training run is NO-GO on this machine until a human-approved base-model manifest, approved immutable dataset version, local model assets, optional training dependencies, and GPU or approved training host are available.
- MongoDB bootstrap mutates the configured database and should be run manually only after confirming the target database.

## Manual Setup Requirements

```powershell
uv sync
npm install
npm --prefix apps/web install
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
uv run devmind-training inspect-hardware
scripts/dev.ps1
```

Unix-like:

```sh
uv sync
npm install
npm --prefix apps/web install
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
uv run devmind-training inspect-hardware
./scripts/dev.sh
```

## Phase 4 Approval

Phase 4 is not approved in this task. Recommended next scope is authentication/authorization, governance hardening, and operator workflow hardening before shared deployment. NO-GO for production/shared deployment until real access control and operational policies are implemented.
