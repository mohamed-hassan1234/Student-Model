# Learning-Cycle Architecture

A learning cycle is a bounded, resumable planning record in `learning_cycles`.

Statuses are `planned`, `collecting`, `generating`, `verifying`, `awaiting_review`, `approved`, `rejected`, `completed`, `failed`, and `cancelled`. Cycles record objectives, selected sources, teacher set, generation configuration, verification thresholds, maximum examples, budget limits, owner, metrics, and failure reason.

Phase 2 implements deterministic planning and generation foundations. It does not run infinite loops, autonomous self-training, or automatic model promotion.
