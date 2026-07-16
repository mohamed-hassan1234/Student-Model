# Project Status

## Current Phase

Phase 1: Technology Student Knowledge and RAG MVP.

## Current Repository State

Technology Student v0.1 is implemented as a local-first approved-source RAG MVP. The repository includes source registry, policy checks, secure URL/file validation, parsers, normalization, prompt-injection marking, deterministic chunking, mock/local embedding and model provider foundations, MongoDB storage, GridFS upload storage, retrieval, citations, frontend pages, tests, docs, and CI-compatible validation.

## Completed Work

- Moved Phase 0 plan to completed and created active Phase 1 plan.
- Added Technology Student source registry and approval workflow.
- Added parser pipeline for HTML, PDF text extraction, Markdown, and plain text.
- Added file and web security validation, including SSRF and executable-file protections.
- Added prompt-injection risk marking and untrusted-content prompt delimiting.
- Added deterministic chunking and duplicate chunk detection by content hash.
- Added embedding-provider abstraction with deterministic mock and Ollama/local HTTP foundation.
- Added vector-search provider abstraction with MongoDB Vector Search, local FAISS fallback metadata behavior, and deterministic mock retrieval.
- Added MongoDB repositories for sources, reviews, documents, versions, chunks, ingestion jobs/events, retrieval events, evidence, upload metadata, audit events, and vector metadata.
- Added GridFS upload storage through `AsyncGridFSBucket`.
- Added Technology Student RAG answer flow with citations and insufficient-evidence refusal.
- Added API endpoints under `/api/v1/technology`.
- Extended React app with Status, Sources, Technology Student, and Curriculum views.
- Added Phase 1 tests and documentation.

## Work in Progress

Phase 1 MVP implementation and validation are complete. Production hardening remains for later phases.

## Next Work

Create Phase 2: evaluation, source coverage metrics, production-grade retrieval quality, and provider hardening.

## Known Issues

- `npm install` previously reported transitive frontend tooling audit findings. Review with `npm audit` before production hardening.
- PDF extraction is text-only and does not perform OCR.
- Real MongoDB Vector Search index provisioning is environment-specific.
- Local FAISS native dependency packaging is not required by tests and remains an optional environment integration.
- Authentication and authorization are placeholders for future phases.

## Validation Results

- `uv lock`: passed.
- `uv sync`: passed.
- `uv lock --check`: passed.
- `uv sync --locked`: passed.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy`: passed, 39 source files.
- `uv run pytest`: passed, 32 passed and 1 skipped guarded MongoDB integration test.
- `npm --prefix apps/web run lint`: passed.
- `npm --prefix apps/web run typecheck`: passed.
- `npm --prefix apps/web run test:run`: passed, 6 tests.
- `npm --prefix apps/web run build`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`: passed.
- MongoDB connectivity check inside validation: passed.
- Prohibited Docker-file check inside validation: passed.
- Secret-pattern scan inside validation: passed.

## Environment Limitations

- Unix shell script syntax checks were not run because this is a Windows environment without `bash`.
- `scripts/bootstrap_mongodb.py` was not executed during final validation because it mutates the configured MongoDB database; run it manually after confirming the target database.

## Important Decisions

- MongoDB remains the primary database and source of truth.
- Technology Student v0.1 is the only Phase 1 specialist.
- Tests use mock providers and fakes; no paid API, Ollama, internet access, Docker, or production MongoDB is required.
- Source content is always treated as untrusted data.
- Unsupported answers return `insufficient_evidence` rather than unsupported model-memory claims.

## Pending Human Reviews

- Confirm Apache 2.0 copyright/owner text.
- Review Phase 1 source approval and governance policy before ingesting real sources.
- Confirm MongoDB target database before running bootstrap.
- Review npm audit findings.
- Review local model and embedding provider choices before enabling non-mock providers.
