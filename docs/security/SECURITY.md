# Security

## Secret Handling

Secrets must be provided through environment variables or an external secret manager in future deployments. Do not commit credentials, tokens, keys, `.env` files, uploaded documents, generated datasets, or model files.

## MongoDB Credentials

MongoDB credentials belong only in `MONGODB_URI` outside source control. Health and readiness responses must not expose the URI, username, password, host topology, or credentials.

## Input Validation

Pydantic validates configuration. API request validation must use typed request models as new endpoints are added.

## File Upload Security

Upload workflows validate type, size, provenance, permission, and executable-looking content. Uploaded content remains untrusted.

## Network Access

Phase 1 uses local API, local frontend, optional MongoDB, and no paid inference APIs. External providers require explicit approval and configuration.

## Process Boundaries

API, frontend, and worker run as separate local processes. Stop scripts use recorded PIDs and must not kill unrelated processes.

## Dataset Safety

Datasets require provenance, permission, license review, and human approval. Unknown provenance is not acceptable for training examples.

## Prompt Injection and Web-content Risks

Future source ingestion must treat external content as untrusted. Instructions inside documents or web content must not override system policy or approval requirements.

## Human Approval Requirements

Human approval is required before adding new source categories, external providers, ingestion pipelines, training pipelines, or model promotion flows.

## Local Model Risks

Local models can leak sensitive prompts, produce unsafe outputs, or behave inconsistently. Model configuration, logs, and output handling require review before production use.

## Model Deployment Controls

No automatic model download, training, promotion, or deployment is allowed in Phase 3. Model staging requires evaluation evidence, rollback metadata, license review, and human approval.

## Access Control Planning

Authentication and authorization are placeholders in Phase 2. Any shared or production use must add real access controls first.

## Audit Logging

`system_audit_events` is reserved for safe audit metadata. Audit events must not store secrets or raw private content unless explicitly approved by policy.

## No Arbitrary Code Execution

Do not execute untrusted code from documents, datasets, model outputs, or source repositories. Future code-analysis features must be sandboxed by design before implementation.

## No Unauthorized Data Collection

Hidden data collection, scraping closed interfaces, bypassing paywalls, and training on private conversations without consent are prohibited.
## Phase 2 Dataset and Training Safety

Phase 2 adds automated preparation but not automated training. Generated records require source permission, teacher-output permission, verification signals, risk scoring, and explicit human approval before dataset use.

Administrative mutation endpoints use a temporary local placeholder header, `x-devmind-admin: local-admin`, until real authentication is designed. This is not production authorization.

The safe code runner is disabled by default. Arbitrary generated code is not executed on the host, and execution-dependent claims require future isolation and human review.

Dataset exports exclude rejected records, unresolved licenses, records without training permission, teacher outputs without training permission, blocked sources, and evaluation records.

## Phase 3 Training Safety

Phase 3 validates base-model manifests, rejects unresolved licenses and unapproved remote code, records dataset hashes, refuses automatic resume from unknown checkpoints, writes artifacts only under ignored storage paths, and stores artifact hashes in MongoDB. Real access control remains required before shared use.
