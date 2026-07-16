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

No automatic model download, training, promotion, or deployment is allowed in Phase 0. Future model promotion must require evaluation evidence and human approval.

## Access Control Planning

Authentication and authorization are not implemented in Phase 0. Any future user data or administrative functions must add access controls first.

## Audit Logging

`system_audit_events` is reserved for safe audit metadata. Audit events must not store secrets or raw private content unless explicitly approved by policy.

## No Arbitrary Code Execution

Do not execute untrusted code from documents, datasets, model outputs, or source repositories. Future code-analysis features must be sandboxed by design before implementation.

## No Unauthorized Data Collection

Hidden data collection, scraping closed interfaces, bypassing paywalls, and training on private conversations without consent are prohibited.
