# Rate Limiting

Phase 4 records login attempts and applies account lockout after repeated failed logins. A full per-IP rate limiter is not yet implemented.

Current controls:

- Failed login counters on user records.
- Login-attempt event collection.
- Configurable lockout threshold and duration.
- Stable generic login error responses.

Future hardening should add bounded per-IP and per-account request limits without requiring Docker or a paid service.
