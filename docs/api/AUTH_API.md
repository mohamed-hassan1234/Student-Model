# Auth API

All endpoints are under `/api/v1/auth`.

- `POST /login`: returns a short-lived access token, refresh token, CSRF token, session ID, and public user.
- `POST /refresh`: rotates a refresh token. Cookie-based refresh requires `x-csrf-token`.
- `POST /logout`: revokes the current session.
- `POST /logout-all`: revokes all sessions for the current user.
- `GET /me`: reads the current public user and permissions.
- `POST /change-password`: changes the current user password and revokes active sessions.
- `GET /permissions`: lists role permissions.
- `POST /users`: creates a user.
- `GET /users`: lists users.
- `POST /users/{user_id}/roles`: assigns a role.
- `DELETE /users/{user_id}/roles/{role}`: removes a role.
- `POST /users/{user_id}/active`: activates or deactivates a user.
- `POST /users/{user_id}/reset-password`: resets a user password.
- `POST /users/{user_id}/revoke-sessions`: revokes user sessions.

Administrative endpoints require bearer authentication and the documented permission.
