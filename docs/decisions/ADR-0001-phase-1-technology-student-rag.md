# ADR-0001: Phase 1 Technology Student RAG MVP

## Status

Accepted for Phase 1.

## Decision

Implement one specialist, Technology Student v0.1, with an approved-source registry, deterministic ingestion pipeline, MongoDB-backed chunks and embeddings, configurable vector retrieval, local/mock model providers, citations, and insufficient-evidence responses.

## Rationale

This delivers a useful local-first MVP without training, crawling, paid APIs, Docker, or multiple specialist models.

## Consequences

The MVP favors safety, traceability, and testability over broad coverage. Later phases can harden provider integrations, index provisioning, auth, and evaluation.
