# Approval Workflows

Phase 4 approval workflow:

1. A reviewer creates an approval request for a model candidate.
2. A model approver records a model decision.
3. A security reviewer records a security decision.
4. The request becomes approved only when all required decisions are approved by distinct reviewers.
5. An operator can create a manual staging request.
6. An operator can record that a manual assignment occurred outside automatic deployment.

Rejected decisions close the approval request. Approval requests expire after the configured Phase 4 review window, can be cancelled while pending, and reject invalid transitions with `409 Conflict`. Corrections require a new request.

Emergency override is restricted to actors with `emergency.revoke`, requires a reason, records a critical security event, and remains an audit trail mechanism rather than automatic staging or deployment.
