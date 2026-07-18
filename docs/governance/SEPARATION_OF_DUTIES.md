# Separation Of Duties

Manual model staging requires independent governance decisions:

- The requester cannot approve the same request.
- Model approval requires `model_approver`.
- Security approval requires `security_reviewer`.
- A candidate creator cannot provide final model approval for that candidate.
- Required approvals must come from at least two distinct reviewers.
- A single reviewer cannot satisfy multiple approval requirements on the same request.
- Operators may record manual staging only after governance approval.
- Approval requesters cannot execute their own staging request.

These checks are enforced in `GovernanceService`. They do not deploy or promote a model automatically.
