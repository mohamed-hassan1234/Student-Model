# Rollback Workflow

Rollback in Phase 4 is metadata-only.

An operator with `staging.rollback` can mark a manual staging request as rolled back and record the reason. The API records a staging event but does not:

- Change production model configuration.
- Restart services.
- Replace adapters.
- Download or upload model weights.

Future phases may add provider-specific rollback execution after an approved architecture decision.
