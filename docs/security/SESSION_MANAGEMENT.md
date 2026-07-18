# Session Management

Sessions are stored in MongoDB in `auth_sessions`.

- Refresh tokens are hashed before storage.
- Refresh token reuse revokes the refresh-token family, revokes sessions in that family, and records a critical security event.
- Expired sessions cannot use access or refresh tokens.
- Password changes, account deactivation, and explicit session revocation invalidate active sessions.
- Session expiration is indexed for cleanup and operational review.
- Access tokens are not persisted by the frontend; they are held in memory.

Production settings reject insecure auth cookies. Operators should use HTTPS and set `AUTH_COOKIE_SECURE=true` when accessing the API over a secure origin.
