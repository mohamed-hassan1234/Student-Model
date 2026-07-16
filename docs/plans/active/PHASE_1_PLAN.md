# Phase 1 Plan

## Objective

Build Technology Student v0.1: a local-first RAG MVP for a limited technology curriculum using approved sources, MongoDB storage, local/mock embeddings, local/mock model providers, citations, and honest insufficient-evidence responses.

## Milestones

1. Source registry and approval workflow.
2. Secure URL/file validation and parser pipeline.
3. Normalization, prompt-injection marking, deterministic chunking, duplicate detection, and embeddings.
4. MongoDB storage for sources, documents, chunks, ingestion jobs/events, retrieval events, evidence, and vector metadata.
5. Vector retrieval through configurable provider foundations.
6. Technology Student question-answering with citations and refusal on insufficient evidence.
7. API endpoints for sources, uploads, ingestion, student Q&A, curriculum, and capabilities.
8. Frontend Sources, Technology Student, and Curriculum pages.
9. Documentation, tests, validation, and status update.

## Files Affected

`services/api`, `services/worker`, `services/model_gateway`, `apps/web`, `infra/mongodb`, `scripts`, `.env.example`, `docs`, and tests.

## Acceptance Criteria

- Approved HTML, PDF, Markdown, and text sources can be represented and parsed.
- Chunks are traceable to source, document, version, section/page, and policy metadata.
- Embeddings are generated through a provider abstraction and stored with chunks.
- Retrieval returns cited evidence or an insufficient-evidence response.
- Tests use mocks/fakes and require no paid APIs, internet access, Ollama, Docker, or production MongoDB.

## Validation Commands

- `uv lock`
- `uv sync`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy`
- `uv run pytest`
- `npm --prefix apps/web run lint`
- `npm --prefix apps/web run typecheck`
- `npm --prefix apps/web run test:run`
- `npm --prefix apps/web run build`
- `powershell -ExecutionPolicy Bypass -File scripts/validate.ps1`

## Dependencies

Python 3.12, uv, Node.js 20+, npm, MongoDB for local runtime, and optional local model/embedding providers.

## Risks

- Real MongoDB vector search availability varies by environment.
- Local FAISS package availability varies by platform, so the MVP keeps a rebuildable local fallback boundary.
- Web fetching must remain allowlist-based and must not become crawling.
- PDF extraction is text-only and does not perform OCR.

## Security Considerations

Documents are untrusted. Source content is delimited in prompts, prompt-injection signals are recorded, private network targets are blocked, file uploads are size/type checked, and unsupported claims return insufficient evidence.

## Decisions

- Technology Student v0.1 is the only specialist model in Phase 1.
- Mock embeddings and mock model provider remain the default test path.
- MongoDB remains the source of truth for metadata, chunks, embeddings, and audit events.

## Unresolved Items

- Production authentication and authorization.
- Full async GridFS bucket wiring in every target environment.
- Production-grade PDF extraction and OCR.
- Real MongoDB Atlas vector index provisioning.
- Native FAISS dependency packaging.

## Out-of-scope Items

Fine-tuning, model-weight modification, autonomous self-training, multiple students, final DevMind Teacher AI, paid APIs, unrestricted crawling, and closed AI interface scraping.
