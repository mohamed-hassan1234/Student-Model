# DevMind AI

DevMind AI is a local-first, low-cost, modular artificial intelligence learning platform. This repository currently contains Phase 1: Technology Student v0.1, a first approved-source RAG MVP on top of the Phase 0 engineering foundation.

Phase 1 does not implement model fine-tuning, model-weight modification, autonomous self-training, unrestricted crawling, multiple specialist models, final routing, or a DevMind Teacher AI.

## Stack

- Backend: Python 3.12, FastAPI, Pydantic, PyMongo Async API, pytest, Ruff, mypy, uv
- Frontend: React, TypeScript, Vite, Tailwind CSS, Vitest, React Testing Library, ESLint
- Database: MongoDB Community Server locally or MongoDB Atlas via environment URI
- Development: local processes, PowerShell and shell scripts, no Docker
- Phase 1: approved-source registry, parsers, chunking, mock/local embeddings, vector retrieval boundary, grounded answers with citations

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

## License and Data

Source code is licensed under Apache License 2.0. This license does not automatically license datasets, model weights, uploaded documents, generated corpora, or third-party knowledge sources. Each dataset and model requires provenance, permission, and license review.
