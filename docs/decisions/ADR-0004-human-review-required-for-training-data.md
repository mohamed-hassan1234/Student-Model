# ADR-0004: Human Review Required for Training Data

## Status

Accepted for Phase 2.

## Decision

No generated record becomes training-ready until an explicit human review action approves it. Approved dataset versions are immutable; corrections create new versions.

## Rationale

Teacher output and synthetic data are not automatically trustworthy. Human review protects against source-license mistakes, unsupported claims, prompt injection, and synthetic feedback loops.

## Consequences

Automated pipelines can prepare candidates and verification reports, but cannot silently approve training records.
