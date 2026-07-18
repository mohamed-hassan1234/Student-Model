# Project Status

## Phase 0 Status

Complete and audited. Phase 0 provides the repository foundation, Python 3.12 configuration, FastAPI health/readiness endpoints, environment-based configuration, MongoDB lifecycle/readiness ping, structured logging, correlation IDs, central exception handling, React status UI, mock model provider, MongoDB-backed worker foundation, local scripts, CI, and no Docker or relational database dependency.

## Phase 1 Status

Complete and audited. Phase 1 provides Technology Student approved-source registration, policy validation, secure ingestion, parsing, sanitization, normalization, duplicate-aware chunking, embeddings, MongoDB storage, GridFS upload metadata, retrieval, local/mock provider generation, citations, insufficient-evidence behavior, prompt-injection isolation, SSRF/file validation, and audit events.

## Phase 2 Status

Complete and audited. Phase 2 provides curriculum coverage, knowledge-gap detection, bounded learning cycles, generated-question records, candidate-answer records, teacher provenance, verification signals, risk scoring, human review, review audit trail, immutable dataset versions, reproducible exports with sidecar manifests, evaluation-set separation, training-config validation, model-candidate registry, and non-deploying recommendations.

## Phase 3 Status

Complete. Phase 3 provides base-model manifest registration/validation, hardware capability inspection, approved dataset entry gate, reproducible split manifests, manual training configuration validation, explicit smoke-training execution, training-run and artifact metadata, baseline unavailable records, candidate mock evaluation records, regression detection, comparison reports, model-candidate registration, advisory deployment recommendations, manual approval actions, adapter load checks, API endpoints, frontend administration pages, docs, and tests. Phase 3 does not automatically download models, start real training, deploy, promote, or change production model settings.

## Phase 4 Status

Validation completed with remediation. Phase 4 adds Argon2 password hashing, JWT access/refresh tokens, refresh-token rotation and reuse detection, refresh-family revocation, session-expiry checks, local users, role-based permissions, authenticated route dependencies, first-super-admin bootstrap command, security events, governance approval requests, model/security approval separation of duties, approval expiry/cancellation, emergency override auditing, manual staging request records, manual assignment metadata, rollback metadata, MongoDB indexes/schema version records, frontend authentication/governance/staging views, and documentation. Phase 4 does not automatically train, deploy, promote, download, upload, replace, or restart model artifacts.

## Phase 5 Status

Blocked at the mandatory entry gate on 2026-07-18. A draft human Phase 4 security review exists at `docs/reviews/PHASE_4_HUMAN_SECURITY_REVIEW.md`, and the sign-off record exists at `docs/reviews/PHASE_4_SECURITY_SIGNOFF_TEMPLATE.md`. The sign-off record is `REVIEW_INCOMPLETE`. The review remains invalid for Phase 5 entry because the required human signoff section still contains placeholder fields for reviewer name, commit confirmation, review date, signature/confirmation, and project-owner acknowledgement. Phase 5 implementation did not begin. No base model was selected, no dataset was finalized, no evaluation set was frozen, no training host was approved, no model artifacts were downloaded, no training configuration was generated, no real training started, and no model was staged, promoted, published, merged, or deployed.

## Audit Status

Phase 0-2 audit completed. Phase 4 validation/security audit completed with technical validation passing and human security review still required. Phase 4 plans were moved to `docs/plans/completed/`. Active plan: `docs/plans/active/PHASE_5_PLAN.md`, currently blocked by an incomplete human security sign-off. Audit reports: `docs/audits/PHASE_0_2_AUDIT_REPORT.md` and `docs/audits/PHASE_4_SECURITY_AUDIT_REPORT.md`.

## Validation Results

Phase 4 human-review bookkeeping on 2026-07-18:

- `git rev-parse HEAD`: passed; current commit `90916b187bc081e5f757d3db23ec589898bea6fa`.
- `git log --oneline -5`: passed.
- Reviewed-commit existence check for the draft-observed commit `3da7e25c571eb6facec059a6608067cd9c702931`: passed.
- Review placeholder scan: failed by policy; required human signoff fields still contain `[ENTER ...]` placeholders in `docs/reviews/PHASE_4_HUMAN_SECURITY_REVIEW.md`.
- Sign-off final decision validation: passed as `REVIEW_INCOMPLETE`.
- Deployment limitation validation: passed; production deployment remains not approved.
- Reviewer identity non-invention check: passed; `docs/reviews/PHASE_4_SECURITY_SIGNOFF_TEMPLATE.md` does not copy unaccepted reviewer identity values.
- Lightweight Markdown link scan: passed, no local Markdown link matches reported.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed, including backend checks, frontend checks, environment check, MongoDB connectivity check, no-Docker check, and secret-pattern scan.

Phase 4 validation/security audit on 2026-07-18:

- `git status --short`: passed.
- `git log --oneline -5`: passed.
- `uv lock --check`: passed.
- `uv sync --locked`: passed.
- `npm ci`: passed, 0 vulnerabilities.
- `npm audit --json`: passed, 0 vulnerabilities.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed.
- `uv run pytest`: passed, 62 passed and 1 skipped guarded MongoDB integration test.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed, 11 passed.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- Prohibited Docker/container filename scan: passed, no matches.
- Runtime/config prohibited dependency scan: passed; only validation-script guard strings were present.
- Placeholder admin bypass scan for `x-devmind-admin` and `local-admin`: passed, no matches.
- Tracked model-weight/generated-dataset artifact scan: passed, no matches.
- `sh -n scripts/dev.sh`, `sh -n scripts/stop.sh`, and `sh -n scripts/validate.sh`: not executed because `sh` is not installed in this Windows environment.

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

Phase 4 validation during implementation on 2026-07-17:

- `uv add argon2-cffi PyJWT`: passed.
- `uv add email-validator`: passed.
- `uv run python -m py_compile services/api/src/devmind_api/routes/auth.py`: passed.
- `uv run python -m py_compile services/api/src/devmind_api/routes/governance.py services/api/src/devmind_api/governance/services.py services/api/src/devmind_api/routes/technology.py services/api/src/devmind_api/routes/learning.py services/api/src/devmind_api/routes/training.py services/api/src/devmind_api/main.py`: passed.
- `uv run python -m py_compile services/api/src/devmind_api/routes/technology.py services/api/src/devmind_api/routes/learning.py services/api/src/devmind_api/routes/training.py scripts/auth_cli.py scripts/training_cli.py`: passed.
- `uv run ruff format services/api/src services/api/tests scripts`: passed and reformatted touched Python files.
- `uv run ruff check services/api/src services/api/tests scripts --fix`: partially executed; import fixes were applied and remaining findings were explicit false positives for JWT type labels and deterministic test credentials, which were annotated.
- A subsequent `uv run ruff check services/api/src services/api/tests scripts` attempt was blocked by the execution environment usage limit before completion. Exact local command: `uv run ruff check services/api/src services/api/tests scripts`.
- Secret-pattern scan (`rg -n "password\\s*=|secret\\s*=|api[_-]?key\\s*=" . --glob '!uv.lock' --glob '!node_modules/**' --glob '!apps/web/dist/**'`): passed, no matches.
- Legacy local-admin authorization scan: passed, no matches.
- Prohibited-technology text scan: reviewed; matches are prohibition statements, historical audit notes, or validation scripts, not implementation dependencies or artifacts.

## Known Limitations

- Phase 4 technical validation passes, but Phase 5 remains NO-GO until a human security reviewer signs off.
- A full per-IP rate limiter is not implemented yet; Phase 4 has login-attempt recording, failed-login counters, and account lockout.
- Unix shell syntax checks were not executed because `sh` is unavailable on this Windows machine.
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
uv run devmind-auth bootstrap-admin --email <admin-email> --username <admin-username> --password "<strong-password>"
uv run devmind-training --access-token <token> inspect-hardware
scripts/dev.ps1
```

Unix-like:

```sh
uv sync
npm install
npm --prefix apps/web install
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
uv run devmind-auth bootstrap-admin --email <admin-email> --username <admin-username> --password "<strong-password>"
uv run devmind-training --access-token <token> inspect-hardware
./scripts/dev.sh
```

## Phase 5 Approval

Phase 5 is not approved. Phase 4 technical validation passed, but Phase 4 human security review is incomplete, Phase 4 security sign-off is recorded as `REVIEW_INCOMPLETE`, Phase 5 preparation gate remains blocked, production deployment is not approved, and real model training is not yet approved. The current decision is **NO-GO** until the draft Phase 4 human security-review record is completed and signed by an authorized human reviewer with `APPROVED_FOR_PHASE_5_PREPARATION` or `CONDITIONALLY_APPROVED_FOR_PHASE_5_PREPARATION`.
