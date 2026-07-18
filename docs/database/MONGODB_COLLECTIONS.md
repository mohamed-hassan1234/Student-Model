# MongoDB Collections

This document lists active DevMind AI collections through Phase 4.

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

## Phase 3 Controlled Training Collections

- `base_model_manifests`: approved open-weight base-model metadata, pinned revisions, tokenizer revisions, license review, fine-tuning permission, remote-code status, hardware estimates, hashes, and approval state. Indexed by `(approval_status, updated_at)`.
- `hardware_capability_reports`: local hardware inspection snapshots with OS, Python, CPU, RAM, GPU/CUDA, precision, disk, recommendation, and limitations. Indexed by `created_at`.
- `training_dataset_validation_reports`: dataset entry-gate reports with approved counts, split counts, distributions, duplicate/leakage/secret checks, token estimates, resource estimates, and blockers. Indexed by `(dataset_version_id, created_at)`.
- `dataset_split_manifests`: reproducible train/validation/held-out test split records with seed, grouped record assignments, and manifest hash. Indexed by `(dataset_version_id, seed)`.
- `training_artifacts`: artifact path, type, SHA-256, size, and run linkage for adapters, checkpoints, metrics, and logs. Indexed by `(training_run_id, artifact_type)`.
- `candidate_comparisons`: candidate-versus-baseline comparison reports with improvements, regressions, safety/citation/performance/resource changes, and recommendation. Indexed by `(candidate_id, created_at)`.
- `model_approvals`: human approval, rejection, or more-evaluation actions for model candidates. Indexed by `(candidate_id, created_at)`.
- `adapter_load_checks`: candidate adapter compatibility/hash/status checks for local provider integration. Indexed by `(candidate_id, checked_at)`.

Shared Phase 2/3 collections extended in Phase 3:

- `training_configs`: now also stores Phase 3 LoRA/QLoRA/mock-smoke effective configuration.
- `training_runs`: now stores manual run metadata, hardware, checkpoints, artifact locations, hashes, status, and safe errors.
- `model_candidates`: now stores Phase 3 candidate adapter metadata and recommendation state in addition to Phase 2 candidate foundations.
- `model_evaluations`: now stores baseline, production, and candidate evaluation scores/unavailable reasons.
- `deployment_recommendations`: now stores advisory Phase 3 recommendation records. Recommendations do not deploy.

## Phase 4 Authentication And Governance Collections

- `users`: local account records with normalized email, username, display name, Argon2 password hash, active/lockout state, login counters, password timestamps, and session revocation version. Indexed by unique `normalized_email` and `(active, created_at)`.
- `roles`: static role registry for operational visibility. Indexed by unique `role`.
- `permissions`: static permission registry for operational visibility. Indexed by unique `permission`.
- `role_permissions`: static role-to-permission mapping. Indexed by unique `(role, permission)`.
- `user_roles`: active role assignments by user. Indexed by unique `(user_id, role)` and `(role, removed)`.
- `auth_sessions`: session metadata with user ID, refresh family, hashed refresh token, refresh token ID, user agent, IP address, revoked flag, expiration, and timestamps. Indexed by `(user_id, revoked)`, unique `refresh_token_hash`, and `expires_at`.
- `refresh_token_families`: refresh-family metadata for rotation/reuse handling. Indexed by `(user_id, revoked)`.
- `login_attempts`: login attempt records with normalized email, success flag, IP address, and timestamp. Indexed by `(normalized_email, created_at)` and `(success, created_at)`.
- `password_reset_events`: reserved administrative password-reset event records. Indexed by `(user_id, created_at)`.
- `security_events`: account lockout, token-reuse, and permission-denial events. Indexed by `(severity, created_at)` and `(event_type, created_at)`.
- `governance_policies`: enabled governance policies and rule metadata. Indexed by unique `policy_id`.
- `approval_workflows`: reserved multi-step workflow records. Indexed by `(status, created_at)`.
- `approval_requests`: model-candidate approval requests with requester, reason, required decisions, expiry, status, and timestamps. Indexed by `(candidate_id, status)` and `(requested_by, created_at)`.
- `approval_decisions`: model/security approval decisions with reviewer identity, reviewer roles, decision type, approval state, notes, and timestamp. Indexed by `(approval_request_id, decision_type)` and `(reviewer_id, created_at)`.
- `staging_requests`: manual staging readiness records with candidate ID, approval request ID, requesting operator, status, target environment, adapter hash, and reason. Indexed by `(candidate_id, status)` and `approval_request_id`.
- `staging_events`: immutable staging event history with actor, result, reason, and risk level. Indexed by `(staging_request_id, created_at)`.
- `production_model_assignments`: metadata records that an operator manually assigned a candidate to a named staging environment. Indexed by `(environment, active)` and `candidate_id`. These records do not change runtime configuration automatically.

## Relationships

MongoDB relationships are represented by document references such as `source_id`, `document_id`, `document_version_id`, `chunk_id`, `question_id`, `candidate_id`, `review_id`, `dataset_candidate_id`, `dataset_version_id`, `evaluation_set_id`, `user_id`, `session_id`, `approval_request_id`, and `staging_request_id`. DevMind does not use relational joins or relational migrations.

## Retention Expectations

Audit, security-event, review, dataset-version, source, schema-version, training-run, artifact-metadata, evaluation, comparison, recommendation, approval, staging, and rollback records should be retained indefinitely until a formal retention policy exists. Session and login-attempt records may receive future TTL cleanup after a reviewed retention decision. Generated export and training artifact files under local storage are rebuildable or reviewable artifacts and must remain ignored by Git.
