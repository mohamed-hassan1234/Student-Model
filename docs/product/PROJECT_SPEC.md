# DevMind AI Project Spec

## Product Vision

DevMind AI will become a local-first, low-cost, modular artificial intelligence learning platform coordinated by specialist student models, a verification layer, an intelligent router, and eventually a central DevMind Teacher AI.

## Intended Users

- Learners who want transparent, source-grounded AI help.
- Developers building local AI learning tools.
- Maintainers curating approved knowledge sources.
- Future educators or teams that need low-cost, inspectable AI assistance.

## Main Problem

Powerful AI learning systems are often expensive, opaque, cloud-dependent, and difficult to constrain to permitted sources. DevMind AI aims to create a foundation for modular local learning assistants with clear provenance and strong boundaries.

## Proposed Solution

The long-term system will coordinate specialist student models trained or adapted only from approved sources. Phase 1 added Technology Student v0.1 RAG for core web and software engineering topics. Phase 2 adds verified dataset-builder foundations without automatic training.

## Goals

- Local-first development and operation.
- Low-cost infrastructure with no required paid API.
- Modular service boundaries.
- MongoDB-backed data and job foundations.
- Clear source, dataset, and model governance.
- Deterministic tests that do not need real MongoDB by default.

## Non-goals

- No automatic model training in Phase 2.
- No unrestricted web crawling in Phase 2.
- No autonomous self-training in Phase 2.
- No final router or DevMind Teacher AI in Phase 2.
- No scraping of closed AI chat interfaces.
- No paid provider dependency.
- No Docker or container-based development.

## Long-term Phases

1. Phase 0: repository and engineering foundation.
2. Phase 1: Technology Student approved-source RAG MVP.
3. Phase 2: verified learning and dataset-builder foundation.
4. Phase 3: authentication, governance hardening, and future approved training experiments.
5. Phase 4: verification and routing prototypes.
6. Phase 5: unified DevMind Teacher AI interface.

## Functional Boundaries

The API exposes health/readiness plus Technology Student endpoints for source registration, ingestion, curriculum, and grounded Q&A. The frontend displays status, sources, chat, and curriculum. The model gateway contains deterministic mock and local HTTP provider foundations.

## Data Boundaries

Phase 1 added source, document, chunk, ingestion, retrieval, evidence, conversation, and vector metadata collections. Phase 2 adds curriculum, question, candidate, verification, review, dataset, evaluation, training-config, and model-candidate metadata. Generated datasets, uploaded documents, local vector indexes, and model artifacts are not committed.

## Future Specialist Student Concept

Each specialist student will focus on a domain, use permitted sources, keep provenance records, and be evaluated before promotion. Technology Student is the only specialist currently implemented.

## Future Router Concept

The router will eventually select specialist models or tools based on question intent, confidence, and verification needs. Phase 2 does not implement the final router.

## Future DevMind Teacher AI Concept

The Teacher AI will provide a unified user interface and coordinate routing, verification, and specialist responses. It is explicitly out of scope for Phase 2.

## Local-first and Low-cost Objectives

Development uses local processes, MongoDB Community Server or an environment-configured Atlas URI, and local model-provider abstractions. No required paid cloud service or paid API is introduced.
## Phase 2 Scope

Phase 2 extends Technology Student v0.1 with verified automated learning preparation and a dataset builder. The system can analyze curriculum coverage, detect gaps, create bounded learning cycles, generate questions, generate candidate answers through approved providers, retrieve evidence, calculate verification and risk signals, require human review, create immutable dataset versions, export approved records, validate training configuration, and register model candidates.

Phase 2 does not automatically train, modify, promote, replace, or deploy model weights.
