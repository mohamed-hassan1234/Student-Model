# Governance API

All endpoints are under `/api/v1/governance`.

- `GET /policies`
- `POST /approval-requests`
- `GET /approval-requests`
- `GET /approval-requests/{approval_request_id}`
- `POST /approval-requests/{approval_request_id}/decisions`
- `POST /approval-requests/{approval_request_id}/cancel`
- `POST /approval-requests/{approval_request_id}/emergency-override`

Approval decisions are permission checked:

- Model decisions require candidate staging approval permission.
- Security decisions require candidate security approval permission.
- The requester cannot approve their own request.
- Duplicate reviewer decisions and invalid workflow transitions return `409 Conflict`.
- Emergency override requires `emergency.revoke`, a reason, and records a critical security event.
