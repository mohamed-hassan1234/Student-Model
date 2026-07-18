# Security Events

Security events are stored in MongoDB in `security_events`.

Recorded examples:

- Account lockout after repeated failed logins.
- Refresh-token reuse detection.
- Attempts to access a route without the required permission.

Security events are operational records and should not contain secrets, raw tokens, passwords, model weights, or uploaded source content.
