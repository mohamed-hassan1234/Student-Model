# Route Permission Matrix

Representative protected routes:

| Route Pattern | Permission |
| --- | --- |
| `POST /api/v1/technology/sources` | `sources.review` |
| `PATCH /api/v1/technology/sources/{source_id}` | `sources.review` |
| `POST /api/v1/technology/sources/{source_id}/review` | `sources.review` |
| `POST /api/v1/technology/ingestion/jobs` | `sources.review` |
| `POST /api/v1/technology/learning/cycles` | `training.configure` |
| `POST /api/v1/technology/learning/cycles/{cycle_id}/start` | `training.start` |
| `POST /api/v1/technology/learning/reviews/{review_id}/approve` | `datasets.approve` |
| `POST /api/v1/technology/learning/dataset-versions/{dataset_version_id}/export` | `datasets.export` |
| `POST /api/v1/technology/training/hardware/inspect` | `training.configure` |
| `POST /api/v1/technology/training/runs/{run_id}/smoke-train` | `training.start` |
| `POST /api/v1/technology/training/candidates` | `candidates.create` |
| `POST /api/v1/technology/training/candidates/{candidate_id}/approve-for-manual-staging` | `candidates.stage_approve` |
| `POST /api/v1/governance/approval-requests` | `candidates.review` |
| `POST /api/v1/governance/approval-requests/{approval_request_id}/decisions` | model or security approval permission |
| `POST /api/v1/governance/staging-requests` | `staging.execute` |
| `POST /api/v1/governance/staging-requests/{staging_request_id}/rollback` | `staging.rollback` |

Public read/status routes remain available where they do not expose secrets or administrative mutation controls.
