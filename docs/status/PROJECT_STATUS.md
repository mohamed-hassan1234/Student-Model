# Project Status

## Phase 0 Status

Complete and audited. Phase 0 provides the repository foundation, Python 3.12 configuration, FastAPI health/readiness endpoints, environment-based configuration, MongoDB lifecycle/readiness ping, structured logging, correlation IDs, central exception handling, React status UI, mock model provider, MongoDB-backed worker foundation, local scripts, CI, and no Docker or relational database dependency.

## Phase 1 Status

Complete and audited. Phase 1 provides Technology Student approved-source registration, policy validation, secure ingestion, parsing, sanitization, normalization, duplicate-aware chunking, embeddings, MongoDB storage, GridFS upload metadata, retrieval, local/mock provider generation, citations, insufficient-evidence behavior, prompt-injection isolation, SSRF/file validation, and audit events.

## Phase 2 Status

Complete and audited. Phase 2 provides curriculum coverage, knowledge-gap detection, bounded learning cycles, generated-question records, candidate-answer records, teacher provenance, verification signals, risk scoring, human review, review audit trail, immutable dataset versions, reproducible exports with sidecar manifests, evaluation-set separation, training-config validation, model-candidate registry, and non-deploying recommendations.

## Audit Status

Phase 0-2 audit completed. Active plan: `docs/plans/active/PHASE_0_2_AUDIT_PLAN.md`. Audit report: `docs/audits/PHASE_0_2_AUDIT_REPORT.md`.

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

## Known Limitations

- Administrative authorization is a placeholder header and not production security.
- Teacher generation is deterministic mock output by default.
- Safe Code Runner is disabled and no arbitrary generated code is executed.
- Training configuration validation does not download models or start training.
- MongoDB bootstrap mutates the configured database and should be run manually only after confirming the target database.

## Manual Setup Requirements

```powershell
uv sync
npm install
npm --prefix apps/web install
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
scripts/dev.ps1
```

Unix-like:

```sh
uv sync
npm install
npm --prefix apps/web install
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
./scripts/dev.sh
```

## Phase 3 Approval

GO for Phase 3 development after human review of the audit report. Recommended Phase 3 scope is authentication/authorization, governance hardening, operator workflows, and operational safety. NO-GO for production/shared deployment until real access control and operational policies are implemented.
