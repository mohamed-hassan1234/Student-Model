# Phase 4 Plan

## Objective

Implement local-first authentication, authorization, governance enforcement, and manual model staging controls. Phase 4 replaces the placeholder administrative header as a normal authorization mechanism with authenticated users, explicit permissions, separation-of-duty policy checks, auditable approval workflows, and manual staging/rollback foundations.

Phase 4 must not start real model training, create multiple specialist models, implement the intelligent router, automatically stage a model, automatically promote a model, add Docker, add a relational database, or require a paid authentication provider.

## Initial Findings

- Current sensitive learning and training routes used a local administrative placeholder before Phase 4 remediation.
- Current Technology Student source/upload/ingestion mutation routes do not enforce real authentication.
- Frontend review actions sent the temporary local admin mechanism directly before Phase 4 remediation.
- Phase 3 status identifies real authorization as the blocker before shared use.
- Worktree before Phase 4 planning was clean; recent commit is `3da7e25 feat: implement controlled model training and evaluation`.

## Milestones

1. Add authentication domain models, repository, services, password hashing, signed-token handling, refresh-token rotation, session revocation, failed-login lockout, and bootstrap-admin CLI.
2. Add role/permission definitions, effective-permission resolution, route authorization dependencies, authenticated audit events, security events, and rate-limiting foundation.
3. Replace legacy placeholder-header dependencies on all sensitive Technology, Learning, and Training routes with permission-based dependencies.
4. Add governance policies, separation-of-duty service, approval requests/decisions, model staging requests/events, staging assignment records, verification states, and rollback controls.
5. Add authentication/admin/governance/staging API routes and route-permission matrix documentation.
6. Add frontend authentication state, login/profile/user-admin/role-admin/governance/model-approval/manual-staging pages, permission-aware actions, and session handling.
7. Update MongoDB indexes, validators, schema version metadata, docs, AGENTS, README, architecture, security, and status.
8. Add deterministic tests for auth, authorization, separation of duties, governance, staging, audit/security events, protected routes, and frontend auth states.
9. Run backend, frontend, security, and repository guardrail validation.

## Files Affected

- `pyproject.toml`, `uv.lock`
- `.env.example`
- `services/api/src/devmind_api/config.py`
- `services/api/src/devmind_api/main.py`
- `services/api/src/devmind_api/auth/*`
- `services/api/src/devmind_api/governance/*`
- `services/api/src/devmind_api/routes/auth.py`
- `services/api/src/devmind_api/routes/admin.py`
- `services/api/src/devmind_api/routes/governance.py`
- `services/api/src/devmind_api/routes/learning.py`
- `services/api/src/devmind_api/routes/technology.py`
- `services/api/src/devmind_api/routes/training.py`
- `scripts/auth_cli.py`
- `scripts/bootstrap_mongodb.py`
- `infra/mongodb/indexes/system_indexes.json`
- `infra/mongodb/validators/system_validators.json`
- `infra/mongodb/schema_versions/phase_4.json`
- `apps/web/src/api/client.ts`
- `apps/web/src/App.tsx`
- `apps/web/src/components/*`
- `services/api/tests/*`
- `apps/web/src/App.test.tsx`
- `docs/security/*`
- `docs/governance/*`
- `docs/models/*`
- `docs/operations/*`
- `docs/api/*`
- `docs/database/MONGODB_COLLECTIONS.md`
- `docs/status/PROJECT_STATUS.md`
- `AGENTS.md`, `README.md`, `ARCHITECTURE.md`

## Acceptance Criteria

- The legacy local admin mechanism is removed from normal authorization paths.
- Local administrator bootstrap exists and does not create a default password.
- Passwords are hashed with a maintained library and never stored plaintext.
- Login, logout, refresh rotation, logout-all, current-user profile, password change, reset, activation, deactivation, and session revocation work.
- Roles map to explicit permissions and backend dependencies enforce permissions.
- Sensitive source, dataset, training, evaluation, candidate, staging, and rollback routes require appropriate permissions.
- Separation-of-duty policy is centralized and tested.
- Model staging requires approval workflow gates and explicit operator action.
- Production assignment is not changed automatically.
- Authenticated audit and security events are recorded without secrets.
- Frontend has login, profile, admin, governance, approval, and staging views.
- Tests and validation pass.

## Validation Commands

- `uv lock --check`
- `uv sync --locked`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy`
- `uv run pytest`
- `npm ci`
- `npm audit --json`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run typecheck`
- `npm --prefix apps/web run test:run`
- `npm --prefix apps/web run build`
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`
- Placeholder-admin-header scan
- Unsafe default-secret scan
- Secret-pattern scan
- No-Docker scan
- No-relational-database scan
- Tracked-generated-artifact scan

## Risks

- JWT/cookie behavior must remain secure for local development without creating unsafe defaults.
- The current fake MongoDB test helper may need modest expansion to support auth queries.
- Retrofitting route authorization can break existing tests until fixtures authenticate users.
- Real production-grade auth still needs deployment review, TLS, secure cookie settings, and operational secret management.

## Security Considerations

- JWT signing keys must come from environment variables or ignored local secret files.
- The API must reject unsafe signing secrets outside test mode.
- Refresh tokens are stored only as hashes.
- State-changing cookie-authenticated routes require CSRF controls.
- Audit events must include authenticated actor/session where available and must never store passwords or raw tokens.
- Emergency overrides require reason and high-severity audit/security events.

## Out Of Scope

Real model training, multiple specialist models, intelligent router, automatic model staging, automatic model promotion, production service restarts, paid auth providers, Docker, relational databases, and Phase 5.
