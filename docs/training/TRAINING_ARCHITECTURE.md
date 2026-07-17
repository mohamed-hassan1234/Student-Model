# Training Architecture

Phase 3 adds controlled LoRA/QLoRA preparation, smoke training, evaluation, and model-candidate metadata for Technology Student v0.1. Training is manual only. API startup, frontend startup, tests, CI, dependency installation, and MongoDB bootstrap never start training.

MongoDB stores base-model manifests, dataset validation reports, split manifests, training runs, artifact metadata, evaluations, comparisons, recommendations, approvals, and rollback metadata. Generated adapters, checkpoints, metrics, logs, and manifests stay under ignored `storage/generated/` paths.

Real LoRA training requires an approved base-model manifest, an approved immutable dataset version, a split manifest, sufficient hardware, optional local training dependencies, and explicit operator invocation. The smoke-training path writes tiny mock artifacts only and does not imply model quality.
