# Evaluation-Leakage Policy

Evaluation records are frozen separately from training records.

Dataset exports exclude records whose `evaluation_set_exclusion_status` marks them as evaluation records. Leakage checks must compare content hashes and record identifiers before export.

If leakage is detected, the record is rejected or held for human review.
