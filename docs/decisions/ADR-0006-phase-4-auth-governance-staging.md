# ADR-0006: Phase 4 Auth, Governance, And Manual Staging

## Status

Accepted.

## Context

DevMind Phase 3 created model-candidate and advisory recommendation records but intentionally did not implement production authorization or automatic deployment. Phase 4 needs local-first controls before any shared operation.

## Decision

Implement local authentication with Argon2 password hashing, short-lived JWT access tokens, rotating hashed refresh tokens, MongoDB-backed sessions, role-based permissions, governance approval requests, independent model/security decisions, manual staging records, and rollback metadata.

The system will not use a paid identity provider, Docker, a relational database, automatic model deployment, or automatic model promotion.

## Consequences

- Administrative APIs require bearer authentication and explicit permissions.
- Browser refresh uses HttpOnly cookies plus CSRF checks.
- First super administrator creation is an explicit manual command.
- Manual staging records are metadata and do not change production model configuration.
- Full production-grade rate limiting and external SSO remain future work.
