# Governance Policies

The default Phase 4 policy is `policy_manual_model_staging_v1`.

It requires:

- Distinct model and security reviewers.
- No requester self-approval.
- Explicit manual staging request.
- No automatic production switch.
- Audit and staging event records for each important action.

Policies are stored in MongoDB and can be inspected through `/api/v1/governance/policies` by users with governance management permission.
