# Static Code Verification

Static checks look for high-risk generated-code signals such as secret patterns, unsafe JavaScript execution patterns, and unsupported execution claims.

Because Docker is prohibited and no approved isolation backend exists in Phase 2, arbitrary generated code is not executed on the host. Execution-dependent claims must be marked for human review.
