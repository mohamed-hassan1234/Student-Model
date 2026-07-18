# System Architecture

## React Frontend

`apps/web` is a React, TypeScript, Vite, and Tailwind CSS app. It exposes system status, authentication, sources, Technology Student chat, curriculum pages, learning cycles, review queue, dataset registry, Phase 3 training administration, model-candidate registry, governance approvals, and manual staging views.

## FastAPI API

`services/api` contains the FastAPI service. It provides versioned routes under `/api/v1`, OpenAPI metadata, structured logging, request correlation IDs, central exception handling, environment-based configuration, CORS, basic security headers, MongoDB readiness checks, authenticated administrative endpoints, and Technology Student endpoints under `/api/v1/technology`.

## MongoDB Database

MongoDB is the primary database. The API uses PyMongo Async API through a connection manager and dependency provider. Phase 1 stores source registry records, documents, versions, chunks, embeddings, ingestion jobs/events, retrieval events, answer evidence, conversations, messages, audit events, and vector metadata.

## MongoDB-backed Background Job Foundation

`services/worker` uses `system_jobs` as the initial job-state store. Jobs support queued, running, completed, failed, and cancelled states. Claiming uses an atomic find-and-update lease pattern. The worker is inactive unless explicitly enabled.

## Service Boundaries

- Ingestion: approved-source fetch/upload, parsing, normalization, chunking, embeddings, and storage.
- Knowledge: source-grounded chunk and embedding retrieval.
- Learning: Phase 2 curriculum coverage, gap detection, bounded generation, verification, review, dataset-versioning, export, training-prep validation, and model-candidate metadata.
- Training: Phase 3 base-model manifests, hardware reports, dataset gates, split manifests, training-run metadata, smoke training, evaluation, regression, recommendation, approvals, and adapter checks.
- Authentication: Phase 4 local users, Argon2 password hashing, JWT access/refresh tokens, session revocation, role permissions, and security events.
- Governance: Phase 4 approval policies, approval requests, independent model/security decisions, manual staging requests, staging events, and rollback metadata.
- Router: reserved for future routing prototypes; no final router exists.
- Model gateway: contains provider contracts and a deterministic mock provider.

## Future Local Model Providers

Provider contracts prepare for Ollama, llama.cpp-compatible HTTP, vLLM-compatible HTTP, deterministic mock, and explicitly approved external providers. Phase 1 does not require Ollama, download models, or call paid APIs.

## Future Training Pipeline

Phase 3 permits explicit manual smoke training and controlled LoRA/QLoRA preparation. No training runs automatically, no model weights are downloaded automatically, and no model candidate is promoted.

## Future Specialist Models

Specialist student models will be domain-focused and source-permissioned. They will require provenance records, license review, evaluation, and human approval before use.

## Future DevMind Teacher AI

The Teacher AI will eventually coordinate tools and specialist models through one interface. Phase 2 does not implement the final Teacher AI.

## Security Boundaries

Secrets are environment-only. Readiness does not expose credentials. Administrative mutation endpoints require bearer authentication and explicit permissions. File upload workflows, arbitrary code execution, automatic model promotion, hidden data collection, and unauthorized scraping are prohibited.

## Data Flow

Frontend calls API status, auth, source, Technology Student, Phase 2 learning, Phase 3 training, and Phase 4 governance endpoints. API checks local process/configuration and MongoDB ping. Worker may claim jobs from MongoDB when explicitly enabled. Model gateway defaults to deterministic mock responses and can be configured for approved local HTTP providers.

## Process Boundaries

Local development runs API, frontend, and optional worker as separate local processes. PIDs are written under `.devmind/pids` so stop scripts avoid unrelated processes.

## No-Docker Development Model

Development and CI use local process commands only. Docker, Docker Compose, Dockerfiles, Kubernetes, and Testcontainers are not part of this repository.
## Phase 2 Verified Learning Layer

Phase 2 adds `learning_models`, `learning_repositories`, `learning_services`, and `/api/v1/technology/learning` routes beside the Phase 1 Technology Student RAG layer.

The layer includes curriculum planning, source coverage analysis, knowledge-gap detection, bounded learning cycles, deterministic question generation, mock teacher candidate-answer generation, evidence retrieval, verification signals, mandatory human review, dataset candidates, immutable dataset versions, JSONL export, frozen evaluation-set metadata, training-configuration validation, model-candidate registration, deployment recommendations, and rollback metadata.

Generated examples do not become training-ready without human approval. Training does not start automatically, and deployment recommendations do not deploy a model.

## Phase 4 Governance Layer

Phase 4 adds `auth` and `governance` modules plus `/api/v1/auth` and `/api/v1/governance` routes. Sensitive source, learning, training, candidate, and staging routes use permission dependencies. Manual staging records are metadata-only and do not change production model configuration.
