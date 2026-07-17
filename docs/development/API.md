# API

Phase 1 endpoints are under `/api/v1/technology`.

- `POST /sources`
- `GET /sources`
- `GET /sources/{source_id}`
- `PATCH /sources/{source_id}`
- `POST /sources/{source_id}/review`
- `POST /sources/{source_id}/deactivate`
- `GET /sources/{source_id}/history`
- `POST /uploads`
- `GET /uploads/{source_id}/status`
- `GET /uploads/{source_id}/parsing-result`
- `DELETE /uploads/{source_id}`
- `POST /ingestion/jobs`
- `GET /ingestion/jobs`
- `GET /ingestion/jobs/{job_id}`
- `POST /ingestion/jobs/{job_id}/retry`
- `POST /ingestion/jobs/{job_id}/cancel`
- `GET /ingestion/events`
- `POST /student/ask`
- `GET /student/evidence/{retrieval_event_id}`
- `GET /student/retrieval-events/{retrieval_event_id}`
- `GET /student/curriculum`
- `GET /student/capabilities`

Phase 2 endpoints are documented in `docs/development/API_PHASE_2.md`.
