# DevMind AI Agent Guide

## Purpose and Phase

DevMind AI is a local-first, low-cost, modular AI learning platform. The repository is in Phase 0: engineering foundation only. Do not add model training, autonomous learning, final routing, web crawling, or DevMind Teacher AI behavior before an approved later phase.

## Repository Map

- `services/api`: FastAPI API foundation.
- `services/worker`: inactive-by-default MongoDB job worker foundation.
- `services/model_gateway`: future model-provider contracts and deterministic mock provider.
- `apps/web`: React, TypeScript, Vite, Tailwind status app.
- `infra/mongodb`: MongoDB indexes, validators, and schema-version foundation.
- `scripts`: local development, validation, and MongoDB bootstrap scripts.
- `docs`: product, architecture, database, security, governance, setup, validation, plans, and status.
- `storage`: ignored local runtime storage only.

## Sources of Truth

- Product scope: `docs/product/PROJECT_SPEC.md`
- Architecture: `ARCHITECTURE.md` and `docs/architecture/SYSTEM_ARCHITECTURE.md`
- Database rules: `docs/database/MONGODB_ARCHITECTURE.md`
- Source policy: `docs/data-governance/SOURCE_POLICY.md`
- Current plan/status: `docs/plans/active/PHASE_0_PLAN.md`, `docs/status/PROJECT_STATUS.md`

## Standards and Validation

Use Python 3.12, FastAPI, Pydantic, PyMongo Async API, pytest, Ruff, mypy, uv, React, TypeScript, Vite, Tailwind CSS, Vitest, React Testing Library, and ESLint. Required validation is `scripts/validate.ps1` on Windows or `scripts/validate.sh` on Unix-like systems.

## MongoDB Rules

MongoDB is the primary database. Relational databases must not be introduced without an approved architecture decision. Use environment-configured MongoDB URIs and database names, idempotent bootstrap scripts, UTC timestamps, and explicit indexes/validators. Do not add SQLAlchemy, Alembic, Prisma, pgvector, or relational migrations.

## Security and Data Boundaries

Never commit secrets, credentials, uploaded documents, generated datasets, downloaded models, model weights, virtual environments, or build artifacts. Training data must have documented provenance and permission. Closed AI interfaces must not be scraped. Secret values must not appear in health checks, readiness checks, logs, tests, or docs.

## Documentation Rules

Keep implementation and documentation synchronized. Record assumptions, limitations, validation results, and human-review needs in `docs/status/PROJECT_STATUS.md`.

## Prohibited

Do not add Docker, Docker Compose, Dockerfiles, Kubernetes, Testcontainers, paid API requirements, automatic model downloads, unapproved external providers, unauthorized scraping, paywall bypassing, hidden data collection, or model promotion automation.

## Definition of Done

Phase 0 work is done when the foundation starts locally, tests are deterministic without real MongoDB, optional MongoDB integration tests are guarded, all available validations have run, no prohibited files or technologies exist, and status docs reflect the actual result.
