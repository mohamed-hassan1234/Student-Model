# ADR-0005: Phase 3 Controlled LoRA Training

## Status

Accepted for Phase 3.

## Decision

Implement controlled manual LoRA/QLoRA preparation, mock smoke training, evaluation metadata, regression gates, model-candidate registration, and advisory deployment recommendations for Technology Student v0.1.

## Rationale

DevMind needs a reproducible bridge from approved immutable datasets to candidate adapters without automatic downloads, model-weight modification during startup, production promotion, paid APIs, Docker, or relational databases.

## Consequences

Real training remains an explicit operator action requiring approved base-model manifests, approved datasets, sufficient hardware, optional training dependencies, artifact hashing, evaluation, regression checks, rollback metadata, and human approval.
