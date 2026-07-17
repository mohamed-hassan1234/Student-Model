# DevMind AI

DevMind AI is a local-first, low-cost, modular artificial intelligence learning platform. This repository currently contains Phase 2: Verified Automated Learning and Dataset Builder for Technology Student v0.1, built on the approved-source RAG MVP.

Phase 2 prepares reviewable dataset candidates from approved evidence. It does not automatically train, modify, promote, replace, or deploy model weights.

## Stack

- Backend: Python 3.12, FastAPI, Pydantic, PyMongo Async API, pytest, Ruff, mypy, uv
- Frontend: React, TypeScript, Vite, Tailwind CSS, Vitest, React Testing Library, ESLint
- Database: MongoDB Community Server locally or MongoDB Atlas via environment URI
- Development: local processes, PowerShell and shell scripts, no Docker
- Phase 1: approved-source registry, parsers, chunking, mock/local embeddings, vector retrieval boundary, grounded answers with citations
- Phase 2: curriculum coverage, knowledge gaps, bounded learning cycles, generated questions, verified candidate answers, mandatory human review, immutable dataset versions, reproducible JSONL export, training-prep validation, and model-candidate records

## Quick Start

1. Install Python 3.12, uv, Node.js 20+, npm, and MongoDB Community Server or configure MongoDB Atlas.
2. Copy `.env.example` to `.env` and adjust values for your machine.
3. Install dependencies:

```powershell
uv sync
npm install
npm --prefix apps/web install
```

4. Bootstrap MongoDB infrastructure:

```powershell
uv run python scripts/bootstrap_mongodb.py
```

5. Start local development:

```powershell
scripts/dev.ps1
```

Unix-like shells can use:

```sh
./scripts/dev.sh
```

## Common Commands

- Validate environment: `uv run python scripts/check_environment.py`
- Start API: `uv run uvicorn devmind_api.main:app --host 127.0.0.1 --port 8000`
- Start frontend: `npm --prefix apps/web run dev`
- Start worker: `uv run python -m devmind_worker.runner`
- Run all validation: `scripts/validate.ps1` or `./scripts/validate.sh`
- Stop local processes: `scripts/stop.ps1` or `./scripts/stop.sh`
- Technology Student capabilities: `GET /api/v1/technology/student/capabilities`
- Ask Technology Student: `POST /api/v1/technology/student/ask`
- Phase 2 curriculum: `GET /api/v1/technology/learning/curriculum`
- Phase 2 review queue: `GET /api/v1/technology/learning/reviews`
- Validate training config: `POST /api/v1/technology/learning/training-configs/validate`
- Export approved dataset version: `POST /api/v1/technology/learning/dataset-versions/{dataset_version_id}/export`

## License and Data

Source code is licensed under Apache License 2.0. This license does not automatically license datasets, model weights, uploaded documents, generated corpora, or third-party knowledge sources. Each dataset and model requires provenance, permission, and license review.
