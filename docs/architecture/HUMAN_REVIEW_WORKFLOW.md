# Human Review Workflow

Generated records enter `human_reviews` and remain pending until a reviewer approves, rejects, edits and approves, or requests regeneration.

Every action is recorded in `reviewer_actions` and `system_audit_events`. Approved review items cannot be silently overwritten; changes require a new action and, after versioning, a new dataset version.

No generated record becomes training-ready without explicit human approval.
