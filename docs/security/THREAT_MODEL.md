# Phase 1 Threat Model

Risks include SSRF, private network access, malicious HTML, unsafe uploads, MIME spoofing, prompt injection, unsupported claims, credential leakage, poisoned sources, and vector index corruption.

Controls include HTTP/HTTPS-only URLs, private IP blocking, file size/type checks, script/style stripping, prompt-injection flags, source approval gates, citation requirements, insufficient-evidence responses, environment-only secrets, and ignored generated index files.
