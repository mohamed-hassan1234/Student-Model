# FAISS Fallback

The FAISS fallback is optional and local. Source data, metadata, chunks, and embeddings remain in MongoDB. Local index files are generated artifacts ignored by Git and must be rebuildable from MongoDB embeddings.

If a local FAISS package is unavailable, use the mock provider for tests or MongoDB Vector Search where configured.
