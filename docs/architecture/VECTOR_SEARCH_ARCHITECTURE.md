# Vector Search Architecture

Providers:

- MongoDB Vector Search for environments with configured vector indexes.
- Local FAISS fallback as a generated, ignored, rebuildable local index.
- Deterministic mock provider for tests.

MongoDB remains the source of truth for source metadata, documents, chunks, and embeddings. Vector index metadata is recorded in `vector_index_metadata`.
