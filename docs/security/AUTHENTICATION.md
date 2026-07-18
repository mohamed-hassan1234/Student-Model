# Authentication

Phase 4 adds local user authentication for DevMind AI administration.

- Passwords are hashed with Argon2.
- Access tokens are short-lived JWTs.
- Refresh tokens rotate and are stored only as hashes.
- Refresh-token reuse revokes the token family rather than only the current session.
- Browser refresh tokens are issued in HttpOnly cookies with a same-site CSRF cookie.
- `AUTH_JWT_SECRET` is required outside the test environment and must be at least 32 characters.
- Wildcard credentialed CORS origins and insecure production auth cookies are rejected by configuration validation.
- Login failures are recorded and accounts are locked after the configured threshold.

The first super administrator is created manually:

```powershell
uv run devmind-auth bootstrap-admin --email <admin-email> --username <admin-username> --password "<strong-password>"
```

Do not commit credentials, token values, cookies, or exported session data.
