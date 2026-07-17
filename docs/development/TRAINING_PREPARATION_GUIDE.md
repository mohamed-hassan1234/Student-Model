# Training Preparation Guide

Phase 2 validates future training configuration only.

Manual commands:

```powershell
uv run python scripts/check_environment.py
uv run pytest services/api/tests/test_learning_phase2_service.py
```

API operations:

- Validate config: `POST /api/v1/technology/learning/training-configs/validate`
- Export approved dataset: `POST /api/v1/technology/learning/dataset-versions/{dataset_version_id}/export`
- Register model candidate: `POST /api/v1/technology/learning/model-candidates`

These operations do not download large models, start training, require a GPU, or promote a candidate.
