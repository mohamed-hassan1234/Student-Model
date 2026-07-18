# DevMind AI Threat Model

Risks include SSRF, private network access, malicious HTML, unsafe uploads, MIME spoofing, prompt injection, unsupported claims, credential leakage, poisoned sources, and vector index corruption.

Controls include HTTP/HTTPS-only URLs, private IP blocking, file size/type checks, script/style stripping, prompt-injection flags, source approval gates, citation requirements, insufficient-evidence responses, environment-only secrets, and ignored generated index files.
## Phase 2 Threats

Phase 2 adds dataset poisoning, synthetic feedback loops, evaluation leakage, unauthorized review actions, unauthorized dataset approval, silent approved-record changes, unsafe model promotion, unbounded provider calls, and malicious generated code as explicit risks.

Controls include bounded cycles, maximum generated examples, provider budgets, deterministic verification signals, risk scoring, mandatory human review, immutable dataset versions, audit events, evaluation exclusion checks, disabled safe runner defaults, and non-deploying deployment recommendations.

## Phase 4 Threats

Phase 4 adds risks around credential theft, refresh-token replay, unauthorized role assignment, unauthorized approval, approval collusion, requester self-approval, staging misuse, rollback misuse, and audit tampering.

Controls include Argon2 password hashing, short-lived access tokens, hashed rotating refresh tokens, session revocation, login-attempt recording, account lockout, role-based permission checks, security events, requester self-approval rejection, distinct model/security approval requirements, manual staging metadata, and no automatic production switch.
