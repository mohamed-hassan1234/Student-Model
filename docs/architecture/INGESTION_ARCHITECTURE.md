# Ingestion Architecture

Pipeline:

source registration -> policy validation -> allowlist validation -> permission validation -> secure fetch/upload -> content-type validation -> practical malware-risk checks -> extraction -> prompt-injection marking -> sanitization -> normalization -> duplicate detection -> chunking -> metadata attachment -> embedding generation -> MongoDB storage -> vector metadata update -> ingestion report -> audit event.

Each stage fails safely and records ingestion events. Web ingestion is single-source only; unrestricted crawling is prohibited.
