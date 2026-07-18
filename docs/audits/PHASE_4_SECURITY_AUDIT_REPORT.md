# Phase 4 Security Audit Report

## Executive Summary

Phase 4 authentication, authorization, governance, manual staging, and rollback controls were audited and remediated. Backend, frontend, dependency, and Windows project validation now pass. The audit found and fixed refresh-token family revocation gaps, session-expiry enforcement gaps, governance workflow transition gaps, duplicate approval gaps, stale bootstrap examples, and an over-broad validation secret scan.

Final decision: **NO-GO for Phase 5 until human security review is completed.** Technical validation is passing, but the task explicitly requires human review before Phase 5 preparation.

## Files Reviewed

- Repository guidance, README, architecture, environment, dependency manifests, lockfiles, scripts, MongoDB bootstrap/index metadata, Git status, and recent Git history.
- Phase 4 docs under `docs/security`, `docs/governance`, `docs/models`, `docs/api`, `docs/database`, and `docs/status`.
- Auth implementation under `services/api/src/devmind_api/auth`.
- Governance implementation under `services/api/src/devmind_api/governance`.
- Sensitive routes under `services/api/src/devmind_api/routes`.
- Phase 4 tests under `services/api/tests/test_auth_phase4.py` and `services/api/tests/test_governance_phase4.py`.
- Frontend auth/governance/staging API client and components under `apps/web/src`.

## Commands Executed

- `git status --short`: passed.
- `git log --oneline -5`: passed.
- `uv lock --check`: passed.
- `uv sync --locked`: passed.
- `npm ci`: passed, 0 vulnerabilities.
- `npm audit --json`: passed, 0 vulnerabilities.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed.
- `uv run pytest`: passed, 62 passed, 1 skipped guarded MongoDB integration test.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed, 11 passed.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- Prohibited Docker/container filename scan: passed, no matches.
- Runtime/config prohibited dependency scan: passed; only validation-script guard strings found.
- Placeholder admin bypass scan for `x-devmind-admin` and `local-admin`: passed, no matches.
- Tracked model-weight/generated-dataset artifact scan: passed, no matches.
- `sh -n scripts/dev.sh`, `sh -n scripts/stop.sh`, and `sh -n scripts/validate.sh`: not executed because `sh` is not installed in this Windows environment.

## Validation Results

All backend checks, frontend checks, dependency checks, Windows full validation, and repository scans passed after remediation. Optional real MongoDB integration tests remain skipped unless `MONGODB_TEST_URI` is explicitly configured for a safe test database.

## Authentication Findings

Fixed:

- Refresh-token reuse now revokes the refresh-token family and family sessions.
- Expired sessions are rejected for access-token authentication and refresh-token rotation.
- Logout-all clears auth cookies.
- Last super-admin role removal is blocked.
- Pydantic model config was updated to remove a deprecation warning.
- Test fixture email addresses no longer depend on a reserved `.test` email domain.

Remaining limitation:

- Full per-IP rate limiting is still future work; Phase 4 has login-attempt tracking and account lockout.

## Authorization Findings

Sensitive routes use backend permission dependencies. Runtime scans found no `x-devmind-admin`, `local-admin`, or trusted client-header authorization bypass in implementation paths. Viewer users cannot mutate protected training routes in tests.

## Token And Session Findings

Access tokens are short-lived JWTs with issuer, audience, token type, expiration, session ID, and token ID validation. Refresh tokens rotate and are stored only as hashes. Reuse detection creates a critical security event and revokes the token family. Raw refresh tokens are not persisted in MongoDB.

## Governance Findings

Fixed:

- Invalid approval, staging, and rollback transitions now return `409 Conflict`.
- Approval requests now have an expiry window.
- Pending approval requests can be cancelled.
- Emergency override requires `emergency.revoke`, requires a reason, and records a critical security event.
- Governance decisions and staging events now create audit records with authenticated actor metadata.

## Separation-Of-Duty Findings

Fixed:

- Requesters cannot approve their own approval requests.
- Candidate creators cannot provide final model approval.
- A reviewer cannot satisfy multiple approval requirements on one request.
- Duplicate reviewer decisions are rejected.
- Approval requesters cannot execute their own staging request.

## Staging Findings

Manual staging remains metadata-only. The service now checks candidate approval state, deployment recommendation, adapter location/hash, safety status, license status, blocking regressions, rollback metadata, approved governance request, operator permission, and manual staging environment. Assignment recording updates metadata only and does not change runtime model configuration.

## Rollback Findings

Rollback requires `staging.rollback`, a reason, and an eligible staging state. Rollback records staging and audit events. It does not delete artifacts or alter production model configuration automatically.

## MongoDB Findings

Phase 4 collections reviewed:

- `users`
- `roles`
- `permissions`
- `role_permissions`
- `user_roles`
- `auth_sessions`
- `refresh_token_families`
- `login_attempts`
- `password_reset_events`
- `security_events`
- `governance_policies`
- `approval_workflows`
- `approval_requests`
- `approval_decisions`
- `staging_requests`
- `staging_events`
- `production_model_assignments`
- `rollback_records`
- `system_audit_events`

Indexes are documented in `docs/database/MONGODB_COLLECTIONS.md` and bootstrap metadata. No TTL deletion is applied to required audit records.

## Frontend Findings

Frontend auth, governance, and manual staging pages build and test successfully. Access tokens remain in memory. Refresh cookies are HttpOnly when configured by the API. Permission-aware UI remains advisory; backend route dependencies enforce authorization.

## Critical Issues

Resolved:

- Refresh-token reuse did not revoke the token family.
- Expired sessions were not checked during access-token authentication.

## High-Priority Issues

Resolved:

- Governance invalid transitions returned generic 400 responses instead of 409 conflict.
- Approval requests lacked expiry and cancellation controls.
- Duplicate/multi-type approval by one reviewer was not explicitly rejected.
- Emergency override workflow and critical security event were missing.

## Medium-Priority Issues

Resolved:

- Validation secret scan produced false positives against ordinary security code and docs.
- Bootstrap docs used a concrete example admin address instead of placeholders.
- Governance audit coverage was incomplete.

## Low-Priority Issues

Resolved:

- Pydantic class-based config deprecation warning.
- Test fixture email domain rejected by current email validation.

## Problems Fixed

- Auth repository now supports refresh-family lookup/revocation and super-admin role counting.
- Auth service now checks session expiry, revokes refresh families, blocks unsafe last-super-admin removal, and clears logout-all cookies.
- Settings validation rejects wildcard credentialed CORS and insecure production auth cookies.
- Governance service now centralizes expiry, cancellation, emergency override, duplicate reviewer checks, candidate-creator final-approval rejection, staging gates, rollback state checks, and audit/security events.
- Governance API now exposes cancellation and emergency override routes.
- Validation scripts now scan literal secret assignments instead of variable names and docs.
- Phase 4 tests were expanded to cover token reuse, session expiry, disabled login, candidate creator approval rejection, duplicate reviewer rejection, expiry/cancellation, and emergency override security events.

## Remaining Limitations

- Human security review is still required before Phase 5.
- No full per-IP rate limiter exists yet.
- Unix shell syntax checks were not executed because `sh` is unavailable on this Windows machine.
- Optional real MongoDB integration tests were skipped because no explicit safe `MONGODB_TEST_URI` was configured.
- Browser CSRF protection is implemented for cookie-based refresh; other browser state-changing calls primarily rely on bearer auth and backend authorization.

## Human-Review Items

- Review Argon2 parameters and operational password policy.
- Review JWT lifetime, issuer, audience, and signing-secret operational management.
- Review role-permission matrix and emergency override authority.
- Review manual staging and rollback procedures against the operator environment.
- Review audit/security-event retention expectations.
- Review whether Phase 5 requires a full per-IP rate limiter before public network exposure.

## Final Decision For Phase 5

**NO-GO** until a human security reviewer signs off on Phase 4 controls. After human sign-off, the technical validation state supports considering Phase 5 planning without beginning model promotion or production deployment automation.
