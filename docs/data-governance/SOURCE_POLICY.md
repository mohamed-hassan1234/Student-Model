# Source Policy

DevMind AI may use only sources with documented provenance and permission.

Allowed source categories:

- Official documentation.
- Public-domain resources.
- Open-license resources.
- Properly licensed datasets.
- User-owned content with explicit permission.
- Human-created internal content with consent.
- Open-weight models with compatible licenses.
- Approved source-code repositories.
- Research papers whose usage is permitted.
- Content with recorded provenance.

Explicitly prohibited:

- Unauthorized scraping.
- Paywall bypassing.
- Access-control bypassing.
- Automated extraction from closed AI products.
- Hidden data collection.
- Unlicensed book ingestion.
- Training on private user conversations without consent.
- Training examples with unknown provenance.
- Secret or credential ingestion.

Every dataset requires a provenance record, license record, collection method, allowed use, retention expectation, and human approval before training or evaluation use.

Phase 1 Technology Student uses retrieval-only approved sources for HTML, CSS, JavaScript, TypeScript fundamentals, React, Node.js, Express.js, MongoDB, Git, GitHub, and software engineering fundamentals.
## Phase 2 Dataset Use

Source approval for retrieval does not automatically permit training use. Dataset records must preserve provenance, source license metadata, retrieval permission, training permission, teacher provenance, teacher-output training permission, verification scores, human approval, reviewer identity, and leakage status.

Records with unknown provenance, unresolved license status, blocked sources, secret content, or evaluation-set membership must be excluded from training exports.
