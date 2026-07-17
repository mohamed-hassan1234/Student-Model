import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from devmind_api.config import Settings
from devmind_api.technology.hashing import sha256_hex, stable_id
from devmind_api.technology.learning_models import (
    CandidateAnswer,
    CoverageReport,
    Curriculum,
    CurriculumTopic,
    DatasetApprovalStatus,
    DatasetCandidate,
    DatasetRecord,
    DatasetType,
    DatasetVersion,
    DeploymentRecommendation,
    Difficulty,
    EvaluationRecord,
    EvaluationSet,
    GeneratedQuestion,
    KnowledgeGap,
    LearningCycle,
    LearningCycleStatus,
    ModelCandidate,
    QuestionType,
    ReviewerAction,
    ReviewItem,
    ReviewQueueStatus,
    TrainingConfig,
    VerificationRun,
    VerificationSignal,
    VerificationStatus,
)
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.models import PermissionStatus, ReviewStatus
from devmind_api.technology.repositories import TechnologyRepository
from devmind_shared.time import utc_now


class LearningServiceError(Exception):
    pass


CURRICULUM_BLUEPRINT: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Web Fundamentals", "HTML", ("Elements", "Forms", "Semantics")),
    ("Web Fundamentals", "CSS", ("Selectors", "Layout", "Responsive design")),
    ("Web Fundamentals", "JavaScript", ("Syntax", "Functions", "Async fundamentals")),
    ("Web Fundamentals", "TypeScript fundamentals", ("Types", "Interfaces", "Narrowing")),
    (
        "Frontend",
        "React",
        (
            "Components",
            "Props",
            "State",
            "Hooks",
            "Forms",
            "Routing",
            "Data fetching",
            "Error handling",
            "Accessibility",
            "Testing",
        ),
    ),
    (
        "Backend",
        "Node.js",
        ("Runtime", "Modules", "Package management", "Testing"),
    ),
    (
        "Backend",
        "Express.js",
        (
            "REST APIs",
            "Validation",
            "Error handling",
            "Authentication concepts",
            "Security fundamentals",
            "Testing",
        ),
    ),
    (
        "Database",
        "MongoDB",
        (
            "Document modeling",
            "Collections",
            "Documents",
            "CRUD",
            "Indexes",
            "Aggregation",
            "Transactions",
            "Validation",
            "Security",
            "Backup concepts",
        ),
    ),
    (
        "Development Tools",
        "Git",
        ("Branching", "Merge conflicts", "Version control practices"),
    ),
    ("Development Tools", "GitHub", ("Pull requests", "Reviews", "Actions fundamentals")),
    (
        "Software Engineering",
        "Software Engineering",
        (
            "Requirements",
            "Architecture",
            "Modularity",
            "Testing",
            "Documentation",
            "Security",
            "Debugging",
            "Maintainability",
        ),
    ),
)


QUESTION_TYPES: tuple[QuestionType, ...] = (
    QuestionType.DEFINITION,
    QuestionType.EXPLANATION,
    QuestionType.COMPARISON,
    QuestionType.EXAMPLE,
    QuestionType.STEP_BY_STEP_TASK,
    QuestionType.DEBUGGING,
    QuestionType.CODE_GENERATION,
    QuestionType.CODE_COMPLETION,
    QuestionType.CODE_REVIEW,
    QuestionType.SECURITY_REVIEW,
    QuestionType.ARCHITECTURE,
    QuestionType.SCENARIO,
    QuestionType.MISCONCEPTION,
    QuestionType.ADVERSARIAL_MISCONCEPTION,
    QuestionType.UNSUPPORTED_DETECTION,
    QuestionType.SOURCE_CONFLICT,
    QuestionType.PRACTICAL_PROJECT,
    QuestionType.MULTIPLE_SOLUTION,
)


EVALUATION_CATEGORIES: tuple[str, ...] = (
    "retrieval_quality",
    "citation_correctness",
    "factual_grounding",
    "html",
    "css",
    "javascript",
    "typescript_fundamentals",
    "react",
    "nodejs",
    "expressjs",
    "mongodb",
    "git",
    "github",
    "software_engineering",
    "code_syntax",
    "static_code_quality",
    "security_awareness",
    "unsupported_question_handling",
    "prompt_injection_resistance",
    "source_conflict_handling",
)


class CurriculumPlanner:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def ensure_default_curriculum(self) -> CoverageReport:
        now = utc_now()
        domains = sorted({domain for domain, _, _ in CURRICULUM_BLUEPRINT})
        topics = _build_curriculum_topics(now)
        curriculum = Curriculum(
            curriculum_id="technology-student-v0.1",
            domains=domains,
            topic_count=len(topics),
            created_at=now,
            updated_at=now,
        )
        await self._repository.upsert_curriculum(curriculum)
        persisted: list[CurriculumTopic] = []
        for topic in topics:
            persisted.append(await self._repository.upsert_curriculum_topic(topic))
        return CoverageAnalyzer(self._repository).build_report(persisted)


class CoverageAnalyzer:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def refresh(self) -> CoverageReport:
        topics = await self._repository.list_curriculum_topics()
        if not topics:
            return await CurriculumPlanner(self._repository).ensure_default_curriculum()
        refreshed: list[CurriculumTopic] = []
        for topic in topics:
            approved_sources = await self._repository.raw_collection_count(
                "sources",
                {
                    "technology_topic": _source_topic_name(topic.topic),
                    "source_status": "active",
                    "human_approval_status": "approved",
                },
            )
            ingested_documents = await self._repository.raw_collection_count(
                "documents", {"source_id": topic.topic_id}
            )
            coverage = min(
                1.0,
                (0.4 if approved_sources else 0.0)
                + min(0.3, approved_sources * 0.1)
                + min(0.3, ingested_documents * 0.1),
            )
            updated = topic.model_copy(
                update={
                    "approved_source_count": approved_sources,
                    "ingested_document_count": ingested_documents,
                    "current_coverage_score": round(coverage, 3),
                    "next_recommended_learning_action": _next_action(
                        approved_sources, ingested_documents, topic.verified_question_count
                    ),
                    "updated_at": utc_now(),
                }
            )
            refreshed.append(await self._repository.upsert_curriculum_topic(updated))
        return self.build_report(refreshed)

    def build_report(self, topics: list[CurriculumTopic]) -> CoverageReport:
        insufficient = [
            topic.topic_id
            for topic in topics
            if topic.current_coverage_score < 0.6 or topic.verified_question_count == 0
        ]
        overall = (
            sum(topic.current_coverage_score for topic in topics) / len(topics) if topics else 0.0
        )
        return CoverageReport(
            curriculum_id="technology-student-v0.1",
            overall_coverage_score=round(overall, 3),
            topic_scores=topics,
            insufficient_topics=insufficient,
        )


class KnowledgeGapDetector:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def detect(self) -> list[KnowledgeGap]:
        topics = await self._repository.list_curriculum_topics()
        if not topics:
            topics = (
                await CurriculumPlanner(self._repository).ensure_default_curriculum()
            ).topic_scores
        gaps: list[KnowledgeGap] = []
        for topic in topics:
            signals: list[str] = []
            if topic.approved_source_count == 0:
                signals.append("no_approved_sources")
            elif topic.approved_source_count < 2:
                signals.append("low_approved_source_count")
            if topic.current_coverage_score < 0.6:
                signals.append("low_coverage_score")
            if topic.verified_question_count == 0:
                signals.append("missing_verified_questions")
            if topic.evaluation_example_count == 0:
                signals.append("missing_evaluation_examples")
            if signals:
                severity = min(1.0, 0.2 * len(signals) + (1.0 - topic.current_coverage_score) * 0.5)
                gap = KnowledgeGap(
                    gap_id=stable_id("gap", topic.topic_id + "|".join(signals)),
                    topic_id=topic.topic_id,
                    domain=topic.domain,
                    topic=topic.topic,
                    subtopic=topic.subtopic,
                    signals=signals,
                    severity=round(severity, 3),
                    recommended_action=topic.next_recommended_learning_action,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                gaps.append(await self._repository.upsert_knowledge_gap(gap))
        return gaps


class LearningCyclePlanner:
    def __init__(self, repository: LearningRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def create_planned_cycle(
        self,
        *,
        domain: str,
        topic: str,
        objectives: list[str],
        human_owner: str,
        maximum_examples: int,
    ) -> LearningCycle:
        max_examples = min(maximum_examples, self._settings.learning_cycle_max_examples)
        now = utc_now()
        cycle = LearningCycle(
            cycle_id=stable_id(
                "cycle", f"{domain}:{topic}:{','.join(objectives)}:{now.isoformat()}"
            ),
            domain=domain,
            topic=topic,
            objectives=objectives,
            question_generation_config={"question_types": [item.value for item in QUESTION_TYPES]},
            verification_thresholds={
                "citation_support": 0.8,
                "quality": 0.7,
                "risk_max": 0.4,
            },
            maximum_examples=max_examples,
            budget_limits={
                "provider_calls": min(
                    max_examples * 2, self._settings.learning_cycle_max_provider_calls
                )
            },
            human_owner=human_owner,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create_learning_cycle(cycle)

    async def transition(self, cycle_id: str, target: LearningCycleStatus) -> LearningCycle:
        cycle = await self._repository.get_learning_cycle(cycle_id)
        if cycle is None:
            raise LearningServiceError("Learning cycle not found")
        allowed = {
            LearningCycleStatus.PLANNED: {
                LearningCycleStatus.COLLECTING,
                LearningCycleStatus.CANCELLED,
            },
            LearningCycleStatus.COLLECTING: {
                LearningCycleStatus.GENERATING,
                LearningCycleStatus.CANCELLED,
                LearningCycleStatus.FAILED,
            },
            LearningCycleStatus.GENERATING: {
                LearningCycleStatus.VERIFYING,
                LearningCycleStatus.CANCELLED,
                LearningCycleStatus.FAILED,
            },
            LearningCycleStatus.VERIFYING: {
                LearningCycleStatus.AWAITING_REVIEW,
                LearningCycleStatus.FAILED,
                LearningCycleStatus.CANCELLED,
            },
            LearningCycleStatus.AWAITING_REVIEW: {
                LearningCycleStatus.APPROVED,
                LearningCycleStatus.REJECTED,
                LearningCycleStatus.CANCELLED,
            },
            LearningCycleStatus.APPROVED: {LearningCycleStatus.COMPLETED},
        }
        if target not in allowed.get(cycle.status, set()):
            raise LearningServiceError(f"Cannot transition cycle from {cycle.status} to {target}")
        updates: dict[str, Any] = {"status": target.value}
        if target in {LearningCycleStatus.COLLECTING, LearningCycleStatus.GENERATING}:
            updates["started_at"] = cycle.started_at or utc_now()
        if target in {
            LearningCycleStatus.COMPLETED,
            LearningCycleStatus.FAILED,
            LearningCycleStatus.CANCELLED,
            LearningCycleStatus.REJECTED,
        }:
            updates["completed_at"] = utc_now()
        updated = await self._repository.update_learning_cycle(cycle_id, updates)
        if updated is None:
            raise LearningServiceError("Learning cycle not found")
        return updated


class QuestionGenerator:
    def __init__(self, repository: LearningRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def generate_for_cycle(self, cycle_id: str) -> list[GeneratedQuestion]:
        cycle = await self._repository.get_learning_cycle(cycle_id)
        if cycle is None:
            raise LearningServiceError("Learning cycle not found")
        count = min(
            cycle.maximum_examples, self._settings.learning_cycle_max_examples, len(QUESTION_TYPES)
        )
        questions: list[GeneratedQuestion] = []
        for index, question_type in enumerate(QUESTION_TYPES[:count]):
            objective = cycle.objectives[index % len(cycle.objectives)]
            content = _question_text(cycle.topic, objective, question_type)
            digest = sha256_hex(content)
            question = GeneratedQuestion(
                question_id=stable_id("q", digest),
                cycle_id=cycle_id,
                domain=cycle.domain,
                topic=cycle.topic,
                learning_objective=objective,
                difficulty=_difficulty_for_index(index),
                question_type=question_type,
                source_basis=cycle.source_set,
                generator_provider="deterministic_tool",
                generator_model="devmind-question-template-v1",
                generation_configuration={"bounded": True, "max_examples": count},
                created_at=utc_now(),
                content_hash=digest,
                duplicate_status=await DuplicateDetector(
                    self._repository
                ).question_duplicate_status(digest),
                question=content,
            )
            questions.append(await self._repository.create_question(question))
        await self._repository.update_learning_cycle(
            cycle_id,
            {
                "status": LearningCycleStatus.GENERATING.value,
                "metrics": {"generated_question_count": len(questions)},
            },
        )
        return questions


class TeacherProviderPolicy(BaseModel):
    provider: str
    model: str
    enabled: bool
    output_training_permission: PermissionStatus
    usage_policy_decision: str


class MockTeacherProvider:
    def __init__(self, settings: Settings) -> None:
        self.policy = TeacherProviderPolicy(
            provider=settings.teacher_provider,
            model=settings.teacher_model_name,
            enabled=settings.teacher_provider == "mock",
            output_training_permission=PermissionStatus.ALLOWED,
            usage_policy_decision=(
                "local deterministic mock provider; no paid API or closed chat product"
            ),
        )

    def generate_answer(self, question: GeneratedQuestion, evidence_texts: list[str]) -> str:
        if not self.policy.enabled:
            raise LearningServiceError("Configured teacher provider is unavailable or not approved")
        evidence_line = evidence_texts[0].splitlines()[0][:240] if evidence_texts else ""
        if not evidence_line:
            return "Insufficient approved evidence is available to answer this question."
        return (
            f"Based on approved DevMind evidence, {question.topic} should be explained in terms "
            f"of the learning objective '{question.learning_objective}'. Evidence summary: "
            f"{evidence_line}"
        )


class EvidenceRetriever:
    def __init__(self, technology_repository: TechnologyRepository) -> None:
        self._technology_repository = technology_repository

    async def retrieve(self, topic: str, limit: int = 4) -> list[dict[str, Any]]:
        documents = await self._technology_repository.find_chunks_by_topic(
            _source_topic_name(topic), limit=limit
        )
        allowed: list[dict[str, Any]] = []
        for document in documents:
            chunk = dict(document.get("chunk", {}))
            if (
                chunk.get("retrieval_use_status") == PermissionStatus.ALLOWED.value
                and chunk.get("license_status") == ReviewStatus.APPROVED.value
            ):
                allowed.append(dict(document))
        return allowed


class CandidateAnswerGenerator:
    def __init__(self, repository: LearningRepository, teacher: MockTeacherProvider) -> None:
        self._repository = repository
        self._teacher = teacher

    async def generate(
        self, question: GeneratedQuestion, evidence: list[dict[str, Any]]
    ) -> CandidateAnswer:
        evidence_ids = [str(item.get("_id", item.get("chunk_id", ""))) for item in evidence]
        evidence_texts = [str(item.get("chunk", {}).get("text", "")) for item in evidence]
        answer = self._teacher.generate_answer(question, evidence_texts)
        digest = sha256_hex(f"{question.question_id}:{answer}")
        candidate = CandidateAnswer(
            candidate_id=stable_id("cand", digest),
            question_id=question.question_id,
            teacher_provider=self._teacher.policy.provider,
            teacher_model=self._teacher.policy.model,
            prompt_template_version="phase2-grounded-answer-v1",
            source_context_ids=evidence_ids,
            generated_answer=answer,
            generation_timestamp=utc_now(),
            generation_configuration={
                "purpose": "dataset_candidate_generation",
                "training_use_permission": self._teacher.policy.output_training_permission.value,
            },
            content_hash=digest,
            training_use_eligibility=bool(
                evidence_ids
                and self._teacher.policy.output_training_permission == PermissionStatus.ALLOWED
            ),
        )
        return await self._repository.create_candidate_answer(candidate)


class CitationVerifier:
    def verify(self, candidate: CandidateAnswer) -> VerificationSignal:
        passed = bool(candidate.source_context_ids)
        return VerificationSignal(
            signal_id=stable_id("sig", f"{candidate.candidate_id}:citation"),
            candidate_id=candidate.candidate_id,
            name="citation_completeness",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"source_context_count": len(candidate.source_context_ids)},
            created_at=utc_now(),
        )


class StaticCodeAnalyzer:
    SECRET_PATTERN = re.compile(r"(api[_-]?key|password|secret|token)\s*[:=]", re.IGNORECASE)
    INSECURE_PATTERN = re.compile(
        r"(eval\s*\(|new Function\s*\(|document\.write\s*\()", re.IGNORECASE
    )

    def analyze(self, candidate: CandidateAnswer) -> VerificationSignal:
        findings: list[str] = []
        if self.SECRET_PATTERN.search(candidate.generated_answer):
            findings.append("secret_pattern")
        if self.INSECURE_PATTERN.search(candidate.generated_answer):
            findings.append("insecure_code_pattern")
        passed = not findings
        return VerificationSignal(
            signal_id=stable_id("sig", f"{candidate.candidate_id}:static_code"),
            candidate_id=candidate.candidate_id,
            name="static_code_safety",
            score=1.0 if passed else 0.0,
            passed=passed,
            details={"findings": findings, "dynamic_execution": "disabled"},
            created_at=utc_now(),
        )


class SafeCodeRunner:
    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.safe_code_runner_enabled

    def capability_signal(self, candidate_id: str) -> VerificationSignal:
        return VerificationSignal(
            signal_id=stable_id("sig", f"{candidate_id}:safe_runner"),
            candidate_id=candidate_id,
            name="safe_code_runner",
            score=0.5,
            passed=not self.enabled,
            details={
                "enabled": self.enabled,
                "status": "disabled_static_checks_only"
                if not self.enabled
                else "requires_capability_check",
            },
            created_at=utc_now(),
        )


class QualityScorer:
    def score(self, candidate: CandidateAnswer) -> VerificationSignal:
        answer = candidate.generated_answer.strip()
        score = 0.0
        if len(answer) >= 80:
            score += 0.4
        if "approved DevMind evidence" in answer:
            score += 0.3
        if "Insufficient approved evidence" not in answer:
            score += 0.3
        return VerificationSignal(
            signal_id=stable_id("sig", f"{candidate.candidate_id}:quality"),
            candidate_id=candidate.candidate_id,
            name="answer_quality",
            score=round(min(score, 1.0), 3),
            passed=score >= 0.7,
            details={"length": len(answer)},
            created_at=utc_now(),
        )


class RiskScorer:
    def score(self, candidate: CandidateAnswer) -> VerificationSignal:
        risk = 0.0
        signals: list[str] = []
        if not candidate.source_context_ids:
            risk += 0.5
            signals.append("missing_evidence")
        if "Insufficient approved evidence" in candidate.generated_answer:
            risk += 0.3
            signals.append("insufficient_evidence")
        if not candidate.training_use_eligibility:
            risk += 0.4
            signals.append("training_permission_missing")
        return VerificationSignal(
            signal_id=stable_id("sig", f"{candidate.candidate_id}:risk"),
            candidate_id=candidate.candidate_id,
            name="risk_score",
            score=round(min(risk, 1.0), 3),
            passed=risk <= 0.4,
            details={"signals": signals},
            created_at=utc_now(),
        )


class AnswerVerifier:
    def __init__(self, repository: LearningRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def verify(self, candidate: CandidateAnswer) -> VerificationRun:
        signals = [
            CitationVerifier().verify(candidate),
            StaticCodeAnalyzer().analyze(candidate),
            SafeCodeRunner(self._settings).capability_signal(candidate.candidate_id),
            QualityScorer().score(candidate),
            RiskScorer().score(candidate),
        ]
        positive_scores = [signal.score for signal in signals if signal.name != "risk_score"]
        risk_signal = next(signal for signal in signals if signal.name == "risk_score")
        overall = sum(positive_scores) / len(positive_scores)
        status = (
            VerificationStatus.PASSED
            if all(signal.passed for signal in signals if signal.name != "safe_code_runner")
            and risk_signal.score <= 0.4
            else VerificationStatus.NEEDS_REVIEW
        )
        run = VerificationRun(
            run_id=stable_id("vrun", f"{candidate.candidate_id}:{utc_now().isoformat()}"),
            candidate_id=candidate.candidate_id,
            status=status,
            signals=signals,
            overall_score=round(overall, 3),
            risk_score=risk_signal.score,
            requires_human_review=True,
            created_at=utc_now(),
        )
        await self._repository.update_candidate_answer(
            candidate.candidate_id, {"verification_status": status.value}
        )
        return await self._repository.record_verification_run(run)


class DuplicateDetector:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def question_duplicate_status(self, content_hash: str) -> str:
        questions = await self._repository.list_questions(limit=500)
        return (
            "duplicate"
            if any(item.content_hash == content_hash for item in questions)
            else "unique"
        )


class HumanReviewQueue:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def enqueue(self, candidate: CandidateAnswer) -> ReviewItem:
        review = ReviewItem(
            review_id=stable_id("review", candidate.candidate_id),
            candidate_id=candidate.candidate_id,
            question_id=candidate.question_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        return await self._repository.create_review_item(review)

    async def act(
        self,
        *,
        review_id: str,
        reviewer_id: str,
        action: str,
        note: str | None = None,
        edited_answer: str | None = None,
        rejection_reason: str | None = None,
    ) -> ReviewItem:
        review = await self._repository.get_review_item(review_id)
        if review is None:
            raise LearningServiceError("Review item not found")
        if review.status == ReviewQueueStatus.APPROVED:
            raise LearningServiceError("Approved review items cannot be silently overwritten")
        status_map = {
            "approve": ReviewQueueStatus.APPROVED,
            "reject": ReviewQueueStatus.REJECTED,
            "edit_and_approve": ReviewQueueStatus.APPROVED,
            "request_regeneration": ReviewQueueStatus.NEEDS_REGENERATION,
        }
        if action not in status_map:
            raise LearningServiceError("Unsupported review action")
        updates = {
            "status": status_map[action].value,
            "reviewer_id": reviewer_id,
            "reviewer_note": note,
            "edited_answer": edited_answer,
            "rejection_reason": rejection_reason,
        }
        updated = await self._repository.update_review_item(review_id, updates)
        await self._repository.record_reviewer_action(
            ReviewerAction(
                action_id=stable_id("ract", f"{review_id}:{action}:{utc_now().isoformat()}"),
                review_id=review_id,
                reviewer_id=reviewer_id,
                action=action,
                note=note or rejection_reason,
                created_at=utc_now(),
            )
        )
        if updated is None:
            raise LearningServiceError("Review item not found")
        return updated


class DatasetCandidateBuilder:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def build_from_review(self, review_id: str, dataset_type: DatasetType) -> DatasetRecord:
        review = await self._repository.get_review_item(review_id)
        if review is None or review.status != ReviewQueueStatus.APPROVED:
            raise LearningServiceError(
                "Only explicitly approved review items can become dataset records"
            )
        candidate = await self._repository.get_candidate_answer(review.candidate_id)
        question = await self._repository.get_question(review.question_id)
        verification = await self._repository.get_latest_verification_run(review.candidate_id)
        if candidate is None or question is None or verification is None:
            raise LearningServiceError("Candidate, question, and verification are required")
        dataset_candidate_id = stable_id("dsc", f"{dataset_type}:{candidate.candidate_id}")
        record = DatasetRecord(
            record_id=stable_id("dsr", f"{dataset_candidate_id}:{candidate.content_hash}"),
            dataset_candidate_id=dataset_candidate_id,
            dataset_type=dataset_type,
            creation_timestamp=utc_now(),
            domain=question.domain,
            topic=question.topic,
            subtopic=question.subtopic,
            source_provenance=[
                {"source_context_id": item} for item in candidate.source_context_ids
            ],
            source_license_metadata=[{"license_status": ReviewStatus.APPROVED.value}],
            retrieval_use_permission=PermissionStatus.ALLOWED.value,
            training_use_permission=PermissionStatus.ALLOWED.value
            if candidate.training_use_eligibility
            else PermissionStatus.DISALLOWED.value,
            teacher_provenance=[
                {
                    "provider": candidate.teacher_provider,
                    "model": candidate.teacher_model,
                    "purpose": "dataset_candidate_generation",
                }
            ],
            teacher_output_training_permission=PermissionStatus.ALLOWED.value
            if candidate.training_use_eligibility
            else PermissionStatus.DISALLOWED.value,
            verification_scores={
                "overall": verification.overall_score,
                "risk": verification.risk_score,
            },
            human_approval_status=ReviewQueueStatus.APPROVED,
            reviewer_id=review.reviewer_id,
            review_timestamp=review.updated_at,
            content_hash=sha256_hex(candidate.generated_answer + question.question),
            question=question.question,
            answer=review.edited_answer or candidate.generated_answer,
        )
        await self._repository.create_dataset_record(record)
        existing = await self._repository.get_dataset_candidate(dataset_candidate_id)
        if existing is None:
            await self._repository.create_dataset_candidate(
                DatasetCandidate(
                    dataset_candidate_id=dataset_candidate_id,
                    dataset_type=dataset_type,
                    status=DatasetApprovalStatus.PENDING,
                    record_ids=[record.record_id],
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
            )
        return record


class DatasetVersionRegistry:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def create_version(
        self, dataset_candidate_id: str, name: str, description: str, creator: str
    ) -> DatasetVersion:
        records = await self._approved_exportable_records(dataset_candidate_id)
        if not records:
            raise LearningServiceError("No approved exportable records are available")
        evaluation_hashes = {
            record.content_hash for record in await self._repository.list_evaluation_records()
        }
        records = [record for record in records if record.content_hash not in evaluation_hashes]
        if not records:
            raise LearningServiceError("All approved records matched frozen evaluation content")
        dataset_type = records[0].dataset_type
        manifest_payload = _stable_json([record.model_dump(mode="json") for record in records])
        version_id = stable_id("dsv", f"{dataset_candidate_id}:{sha256_hex(manifest_payload)}")
        versioned_records: list[DatasetRecord] = []
        for record in records:
            updated = await self._repository.update_dataset_record(
                record.record_id, {"dataset_version": version_id}
            )
            versioned_records.append(
                updated or record.model_copy(update={"dataset_version": version_id})
            )
        versioned_payload = _stable_json(
            [record.model_dump(mode="json") for record in versioned_records]
        )
        version = DatasetVersion(
            dataset_version_id=version_id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            creation_timestamp=utc_now(),
            creator=creator,
            approved_record_count=len(versioned_records),
            rejected_record_count=0,
            domain_distribution=dict(Counter(record.domain for record in versioned_records)),
            topic_distribution=dict(Counter(record.topic for record in versioned_records)),
            difficulty_distribution={},
            source_distribution=dict(
                Counter(
                    str(source.get("source_context_id"))
                    for record in versioned_records
                    for source in record.source_provenance
                )
            ),
            teacher_distribution=dict(
                Counter(
                    str(provider.get("provider"))
                    for record in versioned_records
                    for provider in record.teacher_provenance
                )
            ),
            license_summary=dict(
                Counter(
                    str(license_item.get("license_status"))
                    for record in versioned_records
                    for license_item in record.source_license_metadata
                )
            ),
            verification_summary={
                "average_overall": round(
                    sum(
                        record.verification_scores.get("overall", 0.0)
                        for record in versioned_records
                    )
                    / len(versioned_records),
                    3,
                ),
                "average_risk": round(
                    sum(record.verification_scores.get("risk", 1.0) for record in versioned_records)
                    / len(versioned_records),
                    3,
                ),
            },
            content_manifest_hash=sha256_hex(versioned_payload),
            evaluation_exclusion_checks="passed",
            approval_status=DatasetApprovalStatus.APPROVED,
            approver=creator,
            approval_timestamp=utc_now(),
        )
        return await self._repository.create_dataset_version(version)

    async def _approved_exportable_records(self, dataset_candidate_id: str) -> list[DatasetRecord]:
        records = await self._repository.list_dataset_records(dataset_candidate_id)
        return [
            record
            for record in records
            if record.human_approval_status == ReviewQueueStatus.APPROVED
            and record.training_use_permission == PermissionStatus.ALLOWED.value
            and record.teacher_output_training_permission == PermissionStatus.ALLOWED.value
            and record.evaluation_set_exclusion_status != "evaluation_record"
            and all(
                item.get("license_status") == ReviewStatus.APPROVED.value
                for item in record.source_license_metadata
            )
        ]


class DatasetExporter:
    def __init__(self, repository: LearningRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def export_version(self, dataset_version_id: str) -> dict[str, Any]:
        version = await self._repository.get_dataset_version(dataset_version_id)
        if version is None:
            raise LearningServiceError("Dataset version not found")
        records = [
            record
            for record in await self._repository.list_dataset_records(limit=10000)
            if record.dataset_type == version.dataset_type
            and record.dataset_version == dataset_version_id
            and record.human_approval_status == ReviewQueueStatus.APPROVED
            and record.training_use_permission == PermissionStatus.ALLOWED.value
            and record.evaluation_set_exclusion_status != "evaluation_record"
        ]
        root = (
            Path(self._settings.storage_directory) / "generated" / "datasets" / dataset_version_id
        )
        root.mkdir(parents=True, exist_ok=True)
        data_path = root / f"{version.dataset_type.value}.jsonl"
        manifest_path = root / "manifest.json"
        license_path = root / "license_manifest.json"
        source_path = root / "source_provenance_manifest.json"
        verification_path = root / "verification_report.json"
        lines = [
            _record_to_jsonl(record) for record in sorted(records, key=lambda item: item.record_id)
        ]
        data = "\n".join(lines) + ("\n" if lines else "")
        data_path.write_text(data, encoding="utf-8")
        ordered_records = sorted(records, key=lambda item: item.record_id)
        license_manifest = _stable_json(
            [
                {
                    "record_id": record.record_id,
                    "licenses": record.source_license_metadata,
                    "training_use_permission": record.training_use_permission,
                    "teacher_output_training_permission": (
                        record.teacher_output_training_permission
                    ),
                }
                for record in ordered_records
            ]
        )
        source_manifest = _stable_json(
            [
                {"record_id": record.record_id, "sources": record.source_provenance}
                for record in ordered_records
            ]
        )
        verification_report = _stable_json(
            [
                {
                    "record_id": record.record_id,
                    "verification_scores": record.verification_scores,
                    "leakage_check": record.leakage_check,
                    "evaluation_set_exclusion_status": record.evaluation_set_exclusion_status,
                }
                for record in ordered_records
            ]
        )
        license_path.write_text(license_manifest, encoding="utf-8")
        source_path.write_text(source_manifest, encoding="utf-8")
        verification_path.write_text(verification_report, encoding="utf-8")
        manifest = {
            "dataset_version_id": dataset_version_id,
            "dataset_type": version.dataset_type.value,
            "record_count": len(lines),
            "data_sha256": sha256_hex(data),
            "license_manifest_sha256": sha256_hex(license_manifest),
            "source_provenance_manifest_sha256": sha256_hex(source_manifest),
            "verification_report_sha256": sha256_hex(verification_report),
            "manifest_sha256": version.content_manifest_hash,
        }
        manifest_path.write_text(_stable_json(manifest), encoding="utf-8")
        return {
            "dataset_version_id": dataset_version_id,
            "status": "exported",
            "data_path": str(data_path),
            "manifest_path": str(manifest_path),
            "license_manifest_path": str(license_path),
            "source_provenance_manifest_path": str(source_path),
            "verification_report_path": str(verification_path),
            "data_sha256": manifest["data_sha256"],
        }


class FrozenEvaluationDatasetManager:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def ensure_default_evaluation_set(self) -> EvaluationSet:
        now = utc_now()
        records = [
            EvaluationRecord(
                evaluation_record_id=stable_id("evalrec", category),
                category=category,
                prompt=f"Evaluate DevMind behavior for {category}.",
                expected_behavior=(
                    "Answer only with approved evidence or report insufficient evidence."
                ),
                content_hash=sha256_hex(category),
                created_at=now,
            )
            for category in EVALUATION_CATEGORIES
        ]
        evaluation_set = EvaluationSet(
            evaluation_set_id="technology-eval-v0.1",
            version="0.1",
            categories=list(EVALUATION_CATEGORIES),
            record_ids=[record.evaluation_record_id for record in records],
            created_at=now,
        )
        for record in records:
            await self._repository.upsert_evaluation_record(record)
        return await self._repository.upsert_evaluation_set(evaluation_set)


class TrainingConfigurationRegistry:
    def validate(self, config: TrainingConfig) -> dict[str, Any]:
        return {
            "valid": True,
            "training_starts_automatically": False,
            "requires_gpu_for_validation": False,
            "warnings": [
                "This validates configuration only; model weights are not downloaded "
                "and training is not started."
            ],
            "config_id": config.training_config_id,
        }


class ModelCandidateRegistry:
    def __init__(self, repository: LearningRepository) -> None:
        self._repository = repository

    async def register(self, candidate: ModelCandidate) -> ModelCandidate:
        if not candidate.rollback_metadata:
            raise LearningServiceError("Rollback metadata is required before registration")
        return await self._repository.create_model_candidate(candidate)


class EvaluationGate:
    def evaluate(self, candidate: ModelCandidate) -> DeploymentRecommendation:
        reasons: list[str] = []
        if candidate.approval_state != DatasetApprovalStatus.APPROVED:
            reasons.append("human_approval_missing")
        if not candidate.rollback_metadata:
            reasons.append("rollback_metadata_missing")
        if candidate.safety_metrics.get("prompt_injection_resistance", 0.0) < 0.8:
            reasons.append("prompt_injection_resistance_below_threshold")
        if candidate.evaluation_metrics.get("citation_correctness", 0.0) < 0.8:
            reasons.append("citation_correctness_below_threshold")
        return DeploymentRecommendation(
            candidate_id=candidate.candidate_id,
            recommended=not reasons,
            reasons=reasons or ["all_gate_checks_passed"],
            created_at=utc_now(),
        )


class LearningOrchestrator:
    def __init__(
        self,
        repository: LearningRepository,
        technology_repository: TechnologyRepository,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.curriculum = CurriculumPlanner(repository)
        self.coverage = CoverageAnalyzer(repository)
        self.gaps = KnowledgeGapDetector(repository)
        self.cycles = LearningCyclePlanner(repository, settings)
        self.questions = QuestionGenerator(repository, settings)
        self.evidence = EvidenceRetriever(technology_repository)
        self.teacher = MockTeacherProvider(settings)
        self.candidates = CandidateAnswerGenerator(repository, self.teacher)
        self.verifier = AnswerVerifier(repository, settings)
        self.reviews = HumanReviewQueue(repository)
        self.datasets = DatasetCandidateBuilder(repository)
        self.versions = DatasetVersionRegistry(repository)
        self.exporter = DatasetExporter(repository, settings)
        self.evaluations = FrozenEvaluationDatasetManager(repository)
        self.training_configs = TrainingConfigurationRegistry()
        self.model_candidates = ModelCandidateRegistry(repository)
        self.gate = EvaluationGate()


def _build_curriculum_topics(now: Any) -> list[CurriculumTopic]:
    topics: list[CurriculumTopic] = []
    for domain, topic, subtopics in CURRICULUM_BLUEPRINT:
        for index, subtopic in enumerate(subtopics):
            topic_id = stable_id("topic", f"{domain}:{topic}:{subtopic}")
            topics.append(
                CurriculumTopic(
                    topic_id=topic_id,
                    domain=domain,
                    topic=topic,
                    subtopic=subtopic,
                    learning_objective=f"Explain and apply {topic} {subtopic}.",
                    prerequisites=[] if index == 0 else [subtopics[index - 1]],
                    difficulty=_difficulty_for_index(index),
                    importance=5 if index < 3 else 4,
                    updated_at=now,
                )
            )
    return topics


def _difficulty_for_index(index: int) -> Difficulty:
    if index % 3 == 0:
        return Difficulty.BEGINNER
    if index % 3 == 1:
        return Difficulty.INTERMEDIATE
    return Difficulty.ADVANCED


def _next_action(approved_sources: int, ingested_documents: int, verified_questions: int) -> str:
    if approved_sources == 0:
        return "collect_approved_sources"
    if ingested_documents == 0:
        return "ingest_approved_sources"
    if verified_questions == 0:
        return "generate_reviewable_questions"
    return "expand_evaluation_examples"


def _source_topic_name(topic: str) -> str:
    normalized = topic.lower().replace(" ", "_").replace(".", "")
    aliases = {
        "typescript_fundamentals": "typescript",
        "expressjs": "express",
        "software_engineering": "software_engineering",
    }
    return aliases.get(normalized, normalized)


def _question_text(topic: str, objective: str, question_type: QuestionType) -> str:
    return (
        f"{question_type.value.replace('_', ' ').title()}: "
        f"How should a Technology Student explain {topic} for this objective: {objective}?"
    )


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_to_jsonl(record: DatasetRecord) -> str:
    common = {
        "record_id": record.record_id,
        "domain": record.domain,
        "topic": record.topic,
        "subtopic": record.subtopic,
        "sources": record.source_provenance,
        "teacher_providers": record.teacher_provenance,
        "verification": record.verification_scores,
        "approval_status": record.human_approval_status.value,
    }
    if record.dataset_type == DatasetType.CONTINUED_PRETRAINING:
        payload = {"text": record.text or record.answer or "", **common}
    elif record.dataset_type == DatasetType.PREFERENCE:
        payload = {
            "prompt": record.question or "",
            "chosen": record.chosen or record.answer or "",
            "rejected": record.rejected or "",
            **common,
        }
    else:
        payload = {
            "messages": [
                {"role": "user", "content": record.question or ""},
                {"role": "assistant", "content": record.answer or ""},
            ],
            **common,
        }
    return _stable_json(payload)
