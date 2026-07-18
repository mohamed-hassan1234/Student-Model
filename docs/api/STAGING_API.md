# Staging API

All endpoints are under `/api/v1/governance`.

- `POST /staging-requests`: creates a manual staging request after governance approval and candidate safety, license, regression, adapter-metadata, and rollback-metadata checks.
- `GET /staging-requests`: lists manual staging requests.
- `POST /staging-requests/{staging_request_id}/record-assignment`: records an operator-confirmed manual assignment.
- `POST /staging-requests/{staging_request_id}/rollback`: records a rollback event.

These endpoints do not deploy, promote, restart, download, upload, or replace model artifacts.
Invalid staging or rollback state transitions return `409 Conflict`.
