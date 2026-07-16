# Chunking Strategy

Chunks are deterministic for the same source, document, version, text, chunk size, and overlap. Each chunk stores source, document, version, original reference, title, section/page where available, character range, token estimate, text, content hash, trust/license/permission metadata, prompt-injection flags, and ingestion timestamp.

Duplicate chunks are removed by content hash. Code blocks are preserved when they fit within configured chunk boundaries.
