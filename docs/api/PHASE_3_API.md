# Phase 3 API

All paths are under `/api/v1/technology/training`.

- Hardware: `POST /hardware/inspect`, `GET /hardware`
- Base models: `POST /base-models`, `POST /base-models/validate`, `GET /base-models`, `GET /base-models/{manifest_id}`, `POST /base-models/{manifest_id}/approve`, `POST /base-models/{manifest_id}/reject`
- Datasets: `POST /datasets/{dataset_version_id}/validate`, `POST /datasets/{dataset_version_id}/splits`, `GET /datasets/{dataset_version_id}/validation-report`
- Training: `POST /configs/validate`, `POST /runs`, `GET /runs`, `GET /runs/{run_id}`, `POST /runs/{run_id}/cancel`, `POST /runs/{run_id}/smoke-train`, `GET /runs/{run_id}/checkpoints`, `GET /runs/{run_id}/metrics`
- Evaluation: `POST /evaluations/baseline-unavailable`, `POST /evaluations/candidate`, `POST /candidates/{candidate_id}/compare`
- Candidates: `POST /candidates`, `GET /candidates`, `GET /candidates/{candidate_id}`, `GET /candidates/{candidate_id}/regression-report`, `POST /candidates/{candidate_id}/recommendation`, approval/reject/request-more-evaluation endpoints, audit history, and adapter-load check.

Mutation and expensive endpoints require `x-devmind-admin: local-admin` as a temporary placeholder.
