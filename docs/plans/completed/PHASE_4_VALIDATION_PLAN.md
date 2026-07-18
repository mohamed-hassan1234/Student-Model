# Phase 4 Validation Plan

## Objective

Complete the Phase 4 validation, security audit, and stabilization gate for local authentication, authorization, governance approval workflows, manual staging metadata, and rollback controls. This plan does not authorize Phase 5 work, real model training, model downloads, model staging, model promotion, or production deployment.

## Current Gate State

Phase 4 technical validation passed on 2026-07-18 after remediation. The gate remains NO-GO for Phase 5 until human security review is completed and recorded. Initial review found and remediation addressed refresh-token family revocation, session-expiry checks, governance state transitions, explicit conflict responses, and governance audit coverage.

## Milestones

1. Mandatory review
   - Read Phase 4 architecture, security, governance, API, database, status, plan, source, tests, scripts, dependency manifests, Git status, and recent Git history.
   - Acceptance: reviewed files and history are listed in the security audit report.

2. Dependency validation
   - Run `uv lock --check`, `uv sync --locked`, `npm ci`, and `npm audit --json`.
   - Acceptance: lockfiles are synchronized; no critical/high npm vulnerability remains; dependencies do not introduce Docker, paid APIs, or relational databases.

3. Backend validation
   - Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, and `uv run pytest`.
   - Acceptance: all backend checks pass without weakening tool configuration.

4. Frontend validation
   - Run `npm --prefix apps/web run lint`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test:run`, and `npm --prefix apps/web run build`.
   - Acceptance: frontend auth, governance, staging, and status pages pass linting, type checking, tests, and production build.

5. Focused security remediation
   - Review and fix authentication, token, session, authorization, governance, separation-of-duty, staging, rollback, audit logging, and MongoDB index issues found by tests or manual audit.
   - Acceptance: no unsafe default JWT secret, plaintext password storage, raw refresh-token persistence, trusted-header bypass, or unprotected sensitive route remains.

6. Project validation and repository scans
   - Run `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`.
   - Run Unix shell syntax checks when `sh` is available: `sh -n scripts/dev.sh`, `sh -n scripts/stop.sh`, `sh -n scripts/validate.sh`.
   - Run or document scans for secrets, Docker files, relational database dependencies, placeholder admin headers, raw refresh-token storage, generated artifacts, and model weights.
   - Acceptance: project validation and scans pass, or environment limitations are recorded exactly.

7. Documentation and final audit report
   - Create `docs/audits/PHASE_4_SECURITY_AUDIT_REPORT.md`.
   - Update `docs/status/PROJECT_STATUS.md` and security/governance/database docs when implementation changes.
   - Acceptance: report records commands executed, findings, fixes, limitations, and a GO or NO-GO decision for Phase 5.

## Files Expected To Be Affected

- `services/api/src/devmind_api/auth/*`
- `services/api/src/devmind_api/governance/*`
- `services/api/src/devmind_api/routes/auth.py`
- `services/api/src/devmind_api/routes/governance.py`
- `services/api/tests/test_auth_phase4.py`
- `services/api/tests/test_governance_phase4.py`
- `apps/web/src/api/client.ts`
- `apps/web/src/App.test.tsx`
- `apps/web/src/components/*`
- `infra/mongodb/indexes/system_indexes.json`
- `scripts/bootstrap_mongodb.py`
- `docs/audits/PHASE_4_SECURITY_AUDIT_REPORT.md`
- `docs/status/PROJECT_STATUS.md`
- Phase 4 security, governance, model staging, rollback, API, and MongoDB documentation as needed.

## Risks

- Security controls may look complete in UI while backend enforcement is incomplete.
- Refresh-token reuse detection may revoke only one session unless token-family revocation is explicitly implemented.
- Governance decisions may be accepted in invalid states unless conflicts return 409.
- Manual staging metadata may be mistaken for production promotion unless docs and APIs remain explicit.
- Validation commands may require dependency cache or network access; failures must be reported honestly.

## Rollback Considerations

All changes are local uncommitted work. Remediation should be small, test-backed, and limited to Phase 4 security and validation issues. Do not revert user or earlier implementation changes unless explicitly requested. If a remediation creates wider breakage, prefer a targeted patch restoring the previous behavior plus a documented NO-GO limitation.

## Out Of Scope

- Phase 5 implementation
- Real model training
- Model downloads or weight changes
- Automatic staging, promotion, deployment, or service restart
- Docker, containers, relational databases, paid APIs, or closed-chat scraping
