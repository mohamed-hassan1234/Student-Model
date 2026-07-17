# Verification Architecture

Candidate answers are not accepted as correct by default.

Phase 2 verification records `verification_runs` and `verification_signals` for citation completeness, static code safety, safe-runner capability, answer quality, and risk. Signals are deterministic where practical and always require human review before dataset readiness.

No single model may approve its own output. Human review and source-license checks remain mandatory.
