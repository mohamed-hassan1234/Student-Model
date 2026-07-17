# MongoDB Collections

This document lists active DevMind AI collections through the Phase 0-2 audit.

## System Collections

- `system_schema_versions`: schema-version markers for Phase 0, Phase 1, Phase 2, and future audit components. Indexed by unique `component`. Retain indefinitely.
- `system_audit_events`: safe audit metadata for source registration, retrieval, verification, review, dataset versioning, and future administrative actions. Indexed by `created_at` and `(event_type, created_at)`. Retain according to future audit policy.
- `system_jobs`: MongoDB-backed worker job state with `job_type`, `state`, attempts, worker/lease metadata, timestamps, payload, and safe error summary. Indexed by `(state, created_at)` and `lease_until`. Retain completed jobs according to future operational policy.

## Phase 1 Technology Student Collections

- `sources`: approved-source registry with source identity, original reference, domain, content type, topic, trust, license, permissions, approval, checksum, status, ingestion status, creator, timestamps, and deactivation reason. Indexes include unique `source_id`, `source_status`, `technology_topic`, and `content_checksum`.
- `source_reviews`: source approval/rejection history. Indexed by `(source_id, created_at)`.
- `uploaded_source_files`: GridFS-adjacent upload metadata with original/sanitized names, MIME type, file size, checksum, permission/license metadata, GridFS file ID, and parsing status. Indexed by `(source_id, upload_timestamp)` and `sha256_checksum`.
- `documents`: current document record by source with title, current version, content hash, ingestion status, and timestamps. Indexed by `source_id` and `content_hash`.
- `document_versions`: immutable document-version metadata with document/source IDs, content hash, extraction warnings, and timestamp. Indexed by `(document_id, created_at)`.
- `document_chunks`: chunk, embedding, topic, source/document IDs, and content hash. Indexes include `(source_id, document_id)`, unique `content_hash`, `technology_topic`, and text index on `chunk.text`.
- `ingestion_jobs`: ingestion job state and safe error metadata. Indexed by `(state, created_at)` and `lease_until`.
- `ingestion_events`: ingestion event log. Indexed by `(source_id, created_at)`.
- `conversations`: future conversation containers. Indexed by `created_at`.
- `messages`: future conversation messages. Indexed by `(conversation_id, created_at)`.
- `retrieval_events`: question, topic, evidence status, confidence, chunk IDs, and timestamp. Indexed by `created_at`.
- `answer_evidence`: citation evidence tied to retrieval events. Indexed by `retrieval_event_id`.
- `vector_index_metadata`: provider metadata for MongoDB Vector Search, local FAISS fallback, or mock index state. Indexed by `provider`.

## Phase 2 Verified Learning Collections

- `curricula`: curriculum root records by student and version. Indexed by `(student_id, version)`.
- `curriculum_topics`: hierarchical topic/subtopic objectives, coverage, quality, counts, gaps, recommended action, and review status. Indexed by `(domain, topic, subtopic)` and unique `topic_id`.
- `learning_cycles`: bounded cycle plans with status, objectives, source/teacher sets, generation config, thresholds, budgets, metrics, owner, and timestamps. Indexed by `(status, created_at)`.
- `knowledge_gaps`: detected gap signals, severity, recommended action, status, and timestamps. Indexed by `(status, severity)`.
- `generated_questions`: bounded generated-question records with topic, objective, provider/model, config, content hash, duplicate status, and review status. Indexed by `(topic, content_hash)` and `content_hash`.
- `candidate_answers`: teacher-generated candidates with provider/model provenance, prompt-template version, source context IDs, generated text, content hash, verification status, and training-use eligibility. Indexed by `(question_id, verification_status)`.
- `verification_runs`: overall verification status, signals, scores, risk, and human-review requirement. Indexed by `(candidate_id, created_at)`.
- `verification_signals`: individual verification signal scores and details. Indexed by `(candidate_id, name)`.
- `human_reviews`: review queue records with candidate/question IDs, status, reviewer metadata, notes, edits, rejection reason, and timestamps. Indexed by `(status, created_at)`.
- `reviewer_actions`: immutable review action log. Indexed by `(review_id, created_at)`.
- `dataset_candidates`: candidate dataset containers with type, state, record IDs, and timestamps. Indexed by `(status, dataset_type)`.
- `dataset_records`: versioned training-candidate records with source provenance, license metadata, permissions, teacher provenance, verification scores, human approval, content hash, leakage check, and evaluation exclusion status. Indexed by `(dataset_candidate_id, content_hash)` and `content_hash`.
- `dataset_versions`: immutable approved dataset versions with distributions, license summary, verification summary, manifest hash, approval metadata, and immutable flag. Indexed by `(dataset_type, creation_timestamp)` and unique `dataset_version_id`.
- `evaluation_sets`: frozen evaluation-set metadata with version, categories, record IDs, and timestamp. Indexed by `version`.
- `evaluation_records`: frozen evaluation prompts and content hashes. Indexed by `(category, content_hash)`.
- `training_configs`: future manual training configuration records. Indexed by `(dataset_version, training_method)`.
- `training_runs`: reserved manual training-run metadata; training is not started automatically. Indexed by `(status, created_at)`.
- `model_candidates`: future model-candidate registry with base model, adapter metadata, dataset/evaluation versions, metrics, approval state, recommendation, and rollback metadata. Indexed by `(approval_state, dataset_version)`.
- `model_evaluations`: future candidate evaluation records. Indexed by `(candidate_id, created_at)`.
- `deployment_recommendations`: non-deploying gate outputs. Indexed by `candidate_id`.
- `rollback_records`: rollback metadata for future model-candidate operations. Indexed by `(candidate_id, created_at)`.

## Relationships

MongoDB relationships are represented by document references such as `source_id`, `document_id`, `document_version_id`, `chunk_id`, `question_id`, `candidate_id`, `review_id`, `dataset_candidate_id`, `dataset_version_id`, and `evaluation_set_id`. DevMind does not use relational joins or relational migrations.

## Retention Expectations

Audit, review, dataset-version, source, and schema-version records should be retained indefinitely until a formal retention policy exists. Generated export files under local storage are rebuildable artifacts and must remain ignored by Git.
