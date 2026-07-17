# Dataset Schemas

Phase 2 supports internal records and JSONL exports for continued pretraining, supervised fine-tuning, and preference candidates.

Each dataset record stores record ID, dataset candidate ID, version, domain, topic, subtopic, source provenance, source license metadata, retrieval permission, training permission, teacher provenance, teacher-output permission, verification scores, human approval, reviewer identity, review timestamp, rejection reason, edit history, content hash, leakage check, and evaluation exclusion status.

Exports include approved records only and are written to ignored local generated storage.
