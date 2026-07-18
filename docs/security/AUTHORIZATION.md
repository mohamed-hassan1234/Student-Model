# Authorization

DevMind uses role-based permissions for administrative routes.

Roles:

- `super_admin`
- `ai_engineer`
- `data_reviewer`
- `security_reviewer`
- `model_approver`
- `operator`
- `viewer`

Permissions are represented as explicit strings such as `training.configure`, `datasets.approve`, and `staging.execute`. API dependencies check permissions before sensitive operations. Unauthorized requests receive a stable `403` error and record a security event.

The former local administrative header is no longer accepted by implementation routes, scripts, or the frontend.
