# Manual Staging Workflow

Phase 4 records manual staging readiness. It does not deploy a model.

Requirements before staging can be recorded:

- Candidate approval state is approved.
- Candidate recommendation is `recommended_for_manual_staging`.
- Candidate adapter metadata includes a non-empty location and hash.
- Candidate safety status is `passed`.
- Candidate license status is `approved`.
- Candidate regression results have no blocking entries.
- Candidate rollback metadata exists.
- Governance approval request is approved.
- Actor has `staging.execute`.
- Staging environment is `manual_staging`.
- Adapter hash is copied from the registered candidate metadata.

The staging event log records readiness, manual assignment records, and rollback events. Recording an assignment updates only metadata; operators must still perform any real local provider configuration by a separate reviewed manual process.
