# System Architecture

## React Frontend

`apps/web` is a React, TypeScript, Vite, and Tailwind CSS app. Phase 1 exposes system status, sources, Technology Student chat, and curriculum pages.

## FastAPI API

`services/api` contains the FastAPI service. It provides versioned routes under `/api/v1`, OpenAPI metadata, structured logging, request correlation IDs, central exception handling, environment-based configuration, CORS, basic security headers, MongoDB readiness checks, and Technology Student endpoints under `/api/v1/technology`.

## MongoDB Database

MongoDB is the primary database. The API uses PyMongo Async API through a connection manager and dependency provider. Phase 1 stores source registry records, documents, versions, chunks, embeddings, ingestion jobs/events, retrieval events, answer evidence, conversations, messages, audit events, and vector metadata.

## MongoDB-backed Background Job Foundation

`services/worker` uses `system_jobs` as the initial job-state store. Jobs support queued, running, completed, failed, and cancelled states. Claiming uses an atomic find-and-update lease pattern. The worker is inactive unless explicitly enabled.

## Service Boundaries

- Ingestion: approved-source fetch/upload, parsing, normalization, chunking, embeddings, and storage.
- Knowledge: source-grounded chunk and embedding retrieval.
- Learning: reserved for future approved training or adaptation workflows.
- Router: reserved for future routing prototypes; no final router exists.
- Model gateway: contains provider contracts and a deterministic mock provider.

## Future Local Model Providers

Provider contracts prepare for Ollama, llama.cpp-compatible HTTP, vLLM-compatible HTTP, deterministic mock, and explicitly approved external providers. Phase 1 does not require Ollama, download models, or call paid APIs.

## Future Training Pipeline

`training` directories are placeholders for future configuration, dataset manifests, evaluation, and pipelines. No training code runs in Phase 0.

## Future Specialist Models

Specialist student models will be domain-focused and source-permissioned. They will require provenance records, license review, evaluation, and human approval before use.

## Future DevMind Teacher AI

The Teacher AI will eventually coordinate tools and specialist models through one interface. Phase 0 only documents the concept and reserves boundaries.

## Security Boundaries

Secrets are environment-only. Readiness does not expose credentials. File upload workflows, arbitrary code execution, automatic model promotion, hidden data collection, and unauthorized scraping are prohibited.

## Data Flow

Frontend calls API status endpoints. API checks local process/configuration and MongoDB ping. Worker may later claim jobs from MongoDB when explicitly enabled. Model gateway returns deterministic mock responses only.

## Process Boundaries

Local development runs API, frontend, and optional worker as separate local processes. PIDs are written under `.devmind/pids` so stop scripts avoid unrelated processes.

## No-Docker Development Model

Development and CI use local process commands only. Docker, Docker Compose, Dockerfiles, Kubernetes, and Testcontainers are not part of this repository.
