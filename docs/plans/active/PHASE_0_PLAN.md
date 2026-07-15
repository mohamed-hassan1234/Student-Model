# Phase 0 Plan

## Objective

Establish the production-quality repository and engineering foundation for DevMind AI without building training, crawling, autonomous learning, the final router, or the DevMind Teacher AI.

## Milestones

1. Repository skeleton, guardrails, license, environment template, and agent guidance.
2. FastAPI backend with configuration, logging, correlation IDs, security headers, exception handling, health, readiness, and MongoDB lifecycle.
3. MongoDB foundation with async connection manager, idempotent bootstrap, validators, indexes, schema-version collection, audit collection, job collection, and GridFS boundary.
4. Worker foundation with MongoDB-backed job states and atomic claim/lease design.
5. Model gateway foundation with deterministic mock provider and future provider configuration contracts.
6. React/Vite/Tailwind frontend with system status page and tests.
7. Local process scripts, root commands, and no-Docker CI.
8. Documentation and validation.

## Tasks

- Create requested directory structure and ignore rules.
- Add Apache License 2.0 source-code license with dataset/model caveats.
- Add `.env.example` and validated Pydantic settings.
- Add backend unit tests using fake MongoDB dependencies.
- Add guarded MongoDB integration-test foundation.
- Add frontend loading, healthy, and unavailable tests.
- Add PowerShell and shell dev, stop, and validation scripts.
- Add GitHub Actions for backend and frontend checks.

## Files Affected

Major areas: `services/api`, `services/worker`, `services/model_gateway`, `packages/shared_python`, `apps/web`, `infra/mongodb`, `scripts`, `.github/workflows`, and `docs`.

## Acceptance Criteria

- Health endpoint returns the required response shape.
- Readiness distinguishes API, configuration, and MongoDB status.
- Unit tests do not require real MongoDB.
- Optional MongoDB tests are marked and guarded.
- Mock provider is deterministic.
- No Docker files or relational database dependencies exist.
- Documentation matches implemented Phase 0 scope.

## Validation Commands

- Milestone 1: `rg --files`
- Milestone 2: `uv run pytest services/api/tests`
- Milestone 3: `uv run python scripts/bootstrap_mongodb.py`
- Milestone 4: `uv run pytest services/worker/tests`
- Milestone 5: `uv run pytest services/model_gateway/tests`
- Milestone 6: `npm --prefix apps/web run test:run`
- Milestone 7: `scripts/validate.ps1` or `./scripts/validate.sh`
- Milestone 8: review `docs/status/PROJECT_STATUS.md`

## Dependencies

Python 3.12, uv, Node.js 20+, npm, and MongoDB Community Server or an explicit MongoDB Atlas URI.

## Risks

- Local MongoDB may not be installed or running.
- Network restrictions may prevent dependency lock generation or package installation.
- Async PyMongo APIs require compatible PyMongo versions.

## Security Considerations

Secrets stay in environment variables. Health and readiness responses do not expose credentials. Uploads, crawling, code execution, model downloads, and model promotion are out of scope.

## Decisions

- MongoDB is the primary database.
- Local processes replace Docker.
- Unit tests use repository and database fakes.
- Phase 0 uses a deterministic mock provider only.

## Unresolved Items

- Final model-provider implementations.
- Human approval workflow details.
- Evaluation metrics for future specialist models.
- Production access control.

## Out-of-scope Items

Training, crawling, autonomous learning, final routing, DevMind Teacher AI, paid APIs, model downloads, uploaded document persistence, and generated datasets.
