# ADR-0002: Vector Search Provider Boundary

## Status

Accepted for Phase 1.

## Decision

Define a provider abstraction for MongoDB Vector Search, optional local FAISS fallback, and deterministic mock retrieval. MongoDB remains the source of truth for chunks, metadata, and embeddings.

## Rationale

Local MongoDB installations may not support vector indexes. A provider boundary lets tests remain deterministic and allows future environments to enable MongoDB Vector Search or FAISS without changing ingestion records.

## Consequences

FAISS index files are generated artifacts and must be ignored by Git. Index corruption must never destroy source data because indexes are rebuildable from MongoDB embeddings.
