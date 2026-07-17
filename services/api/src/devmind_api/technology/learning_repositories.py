from collections.abc import Mapping
from typing import Any, cast

from devmind_api.db import MongoDatabase
from devmind_api.technology.learning_models import (
    CandidateAnswer,
    Curriculum,
    CurriculumTopic,
    DatasetCandidate,
    DatasetRecord,
    DatasetVersion,
    DeploymentRecommendation,
    EvaluationRecord,
    EvaluationSet,
    GeneratedQuestion,
    KnowledgeGap,
    LearningCycle,
    ModelCandidate,
    ReviewerAction,
    ReviewItem,
    TrainingConfig,
    VerificationRun,
    VerificationSignal,
    learning_document,
)
from devmind_shared.time import utc_now


class LearningRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def upsert_curriculum(self, curriculum: Curriculum) -> Curriculum:
        await self._database["curricula"].update_one(
            {"_id": curriculum.curriculum_id},
            {"$set": {"_id": curriculum.curriculum_id, **learning_document(curriculum)}},
            upsert=True,
        )
        return curriculum

    async def upsert_curriculum_topic(self, topic: CurriculumTopic) -> CurriculumTopic:
        await self._database["curriculum_topics"].update_one(
            {"_id": topic.topic_id},
            {"$set": {"_id": topic.topic_id, **learning_document(topic)}},
            upsert=True,
        )
        return topic

    async def list_curriculum_topics(self) -> list[CurriculumTopic]:
        cursor = self._database["curriculum_topics"].find({}).sort("topic_id", 1).limit(500)
        documents = await cursor.to_list(length=500)
        return [CurriculumTopic.model_validate(document) for document in documents]

    async def get_curriculum_topic(self, topic_id: str) -> CurriculumTopic | None:
        document = await self._database["curriculum_topics"].find_one({"_id": topic_id})
        return CurriculumTopic.model_validate(document) if document else None

    async def upsert_knowledge_gap(self, gap: KnowledgeGap) -> KnowledgeGap:
        await self._database["knowledge_gaps"].update_one(
            {"_id": gap.gap_id},
            {"$set": {"_id": gap.gap_id, **learning_document(gap)}},
            upsert=True,
        )
        return gap

    async def list_knowledge_gaps(self, status: str | None = None) -> list[KnowledgeGap]:
        query = {"status": status} if status else {}
        cursor = self._database["knowledge_gaps"].find(query).sort("severity", -1).limit(500)
        documents = await cursor.to_list(length=500)
        return [KnowledgeGap.model_validate(document) for document in documents]

    async def create_learning_cycle(self, cycle: LearningCycle) -> LearningCycle:
        document = learning_document(cycle)
        document["_id"] = cycle.cycle_id
        await self._database["learning_cycles"].insert_one(document)
        await self.record_audit_event(
            "learning_cycle_created", {"cycle_id": cycle.cycle_id, "topic": cycle.topic}
        )
        return cycle

    async def get_learning_cycle(self, cycle_id: str) -> LearningCycle | None:
        document = await self._database["learning_cycles"].find_one({"_id": cycle_id})
        return LearningCycle.model_validate(document) if document else None

    async def list_learning_cycles(self, limit: int = 50, offset: int = 0) -> list[LearningCycle]:
        cursor = (
            self._database["learning_cycles"]
            .find({})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [LearningCycle.model_validate(document) for document in documents]

    async def update_learning_cycle(
        self, cycle_id: str, updates: Mapping[str, Any]
    ) -> LearningCycle | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["learning_cycles"].update_one({"_id": cycle_id}, {"$set": payload})
        return await self.get_learning_cycle(cycle_id)

    async def create_question(self, question: GeneratedQuestion) -> GeneratedQuestion:
        document = learning_document(question)
        document["_id"] = question.question_id
        await self._database["generated_questions"].insert_one(document)
        return question

    async def list_questions(self, limit: int = 50, offset: int = 0) -> list[GeneratedQuestion]:
        cursor = (
            self._database["generated_questions"]
            .find({})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [GeneratedQuestion.model_validate(document) for document in documents]

    async def get_question(self, question_id: str) -> GeneratedQuestion | None:
        document = await self._database["generated_questions"].find_one({"_id": question_id})
        return GeneratedQuestion.model_validate(document) if document else None

    async def create_candidate_answer(self, candidate: CandidateAnswer) -> CandidateAnswer:
        document = learning_document(candidate)
        document["_id"] = candidate.candidate_id
        await self._database["candidate_answers"].insert_one(document)
        return candidate

    async def list_candidate_answers(
        self, limit: int = 50, offset: int = 0
    ) -> list[CandidateAnswer]:
        cursor = (
            self._database["candidate_answers"]
            .find({})
            .sort("generation_timestamp", -1)
            .skip(offset)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [CandidateAnswer.model_validate(document) for document in documents]

    async def get_candidate_answer(self, candidate_id: str) -> CandidateAnswer | None:
        document = await self._database["candidate_answers"].find_one({"_id": candidate_id})
        return CandidateAnswer.model_validate(document) if document else None

    async def update_candidate_answer(
        self, candidate_id: str, updates: Mapping[str, Any]
    ) -> CandidateAnswer | None:
        await self._database["candidate_answers"].update_one(
            {"_id": candidate_id}, {"$set": dict(updates)}
        )
        return await self.get_candidate_answer(candidate_id)

    async def record_verification_run(self, run: VerificationRun) -> VerificationRun:
        document = learning_document(run)
        document["_id"] = run.run_id
        await self._database["verification_runs"].insert_one(document)
        for signal in run.signals:
            await self.record_verification_signal(signal)
        await self.record_audit_event(
            "candidate_verified",
            {
                "candidate_id": run.candidate_id,
                "status": run.status.value,
                "overall_score": run.overall_score,
            },
        )
        return run

    async def record_verification_signal(self, signal: VerificationSignal) -> VerificationSignal:
        document = learning_document(signal)
        document["_id"] = signal.signal_id
        await self._database["verification_signals"].insert_one(document)
        return signal

    async def get_latest_verification_run(self, candidate_id: str) -> VerificationRun | None:
        cursor = (
            self._database["verification_runs"]
            .find({"candidate_id": candidate_id})
            .sort("created_at", -1)
            .limit(1)
        )
        documents = await cursor.to_list(length=1)
        return VerificationRun.model_validate(documents[0]) if documents else None

    async def create_review_item(self, review: ReviewItem) -> ReviewItem:
        document = learning_document(review)
        document["_id"] = review.review_id
        await self._database["human_reviews"].insert_one(document)
        return review

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        document = await self._database["human_reviews"].find_one({"_id": review_id})
        return ReviewItem.model_validate(document) if document else None

    async def list_review_items(
        self, status: str | None = "pending", limit: int = 50, offset: int = 0
    ) -> list[ReviewItem]:
        query = {"status": status} if status else {}
        cursor = (
            self._database["human_reviews"]
            .find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [ReviewItem.model_validate(document) for document in documents]

    async def update_review_item(
        self, review_id: str, updates: Mapping[str, Any]
    ) -> ReviewItem | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["human_reviews"].update_one({"_id": review_id}, {"$set": payload})
        return await self.get_review_item(review_id)

    async def record_reviewer_action(self, action: ReviewerAction) -> ReviewerAction:
        document = learning_document(action)
        document["_id"] = action.action_id
        await self._database["reviewer_actions"].insert_one(document)
        await self.record_audit_event(
            "review_action_recorded",
            {
                "review_id": action.review_id,
                "action": action.action,
                "reviewer": action.reviewer_id,
            },
        )
        return action

    async def list_reviewer_actions(self, review_id: str) -> list[ReviewerAction]:
        cursor = (
            self._database["reviewer_actions"].find({"review_id": review_id}).sort("created_at", 1)
        )
        documents = await cursor.to_list(length=500)
        return [ReviewerAction.model_validate(document) for document in documents]

    async def create_dataset_candidate(self, candidate: DatasetCandidate) -> DatasetCandidate:
        document = learning_document(candidate)
        document["_id"] = candidate.dataset_candidate_id
        await self._database["dataset_candidates"].insert_one(document)
        return candidate

    async def list_dataset_candidates(self) -> list[DatasetCandidate]:
        cursor = self._database["dataset_candidates"].find({}).sort("created_at", -1).limit(100)
        documents = await cursor.to_list(length=100)
        return [DatasetCandidate.model_validate(document) for document in documents]

    async def get_dataset_candidate(self, dataset_candidate_id: str) -> DatasetCandidate | None:
        document = await self._database["dataset_candidates"].find_one(
            {"_id": dataset_candidate_id}
        )
        return DatasetCandidate.model_validate(document) if document else None

    async def create_dataset_record(self, record: DatasetRecord) -> DatasetRecord:
        document = learning_document(record)
        document["_id"] = record.record_id
        await self._database["dataset_records"].insert_one(document)
        return record

    async def get_dataset_record(self, record_id: str) -> DatasetRecord | None:
        document = await self._database["dataset_records"].find_one({"_id": record_id})
        return DatasetRecord.model_validate(document) if document else None

    async def update_dataset_record(
        self, record_id: str, updates: Mapping[str, Any]
    ) -> DatasetRecord | None:
        await self._database["dataset_records"].update_one(
            {"_id": record_id}, {"$set": dict(updates)}
        )
        return await self.get_dataset_record(record_id)

    async def list_dataset_records(
        self, dataset_candidate_id: str | None = None, limit: int = 1000
    ) -> list[DatasetRecord]:
        query = {"dataset_candidate_id": dataset_candidate_id} if dataset_candidate_id else {}
        cursor = (
            self._database["dataset_records"].find(query).sort("creation_timestamp", 1).limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [DatasetRecord.model_validate(document) for document in documents]

    async def create_dataset_version(self, version: DatasetVersion) -> DatasetVersion:
        existing = await self._database["dataset_versions"].find_one(
            {"_id": version.dataset_version_id}
        )
        if existing:
            raise ValueError("Approved dataset versions are immutable and cannot be overwritten")
        document = learning_document(version)
        document["_id"] = version.dataset_version_id
        await self._database["dataset_versions"].insert_one(document)
        await self.record_audit_event(
            "dataset_version_created",
            {
                "dataset_version_id": version.dataset_version_id,
                "record_count": version.approved_record_count,
            },
        )
        return version

    async def get_dataset_version(self, dataset_version_id: str) -> DatasetVersion | None:
        document = await self._database["dataset_versions"].find_one({"_id": dataset_version_id})
        return DatasetVersion.model_validate(document) if document else None

    async def list_dataset_versions(self) -> list[DatasetVersion]:
        cursor = (
            self._database["dataset_versions"].find({}).sort("creation_timestamp", -1).limit(100)
        )
        documents = await cursor.to_list(length=100)
        return [DatasetVersion.model_validate(document) for document in documents]

    async def upsert_evaluation_set(self, evaluation_set: EvaluationSet) -> EvaluationSet:
        await self._database["evaluation_sets"].update_one(
            {"_id": evaluation_set.evaluation_set_id},
            {
                "$set": {
                    "_id": evaluation_set.evaluation_set_id,
                    **learning_document(evaluation_set),
                }
            },
            upsert=True,
        )
        return evaluation_set

    async def upsert_evaluation_record(self, record: EvaluationRecord) -> EvaluationRecord:
        await self._database["evaluation_records"].update_one(
            {"_id": record.evaluation_record_id},
            {"$set": {"_id": record.evaluation_record_id, **learning_document(record)}},
            upsert=True,
        )
        return record

    async def list_evaluation_records(self) -> list[EvaluationRecord]:
        cursor = self._database["evaluation_records"].find({}).sort("category", 1).limit(1000)
        documents = await cursor.to_list(length=1000)
        return [EvaluationRecord.model_validate(document) for document in documents]

    async def list_evaluation_sets(self) -> list[EvaluationSet]:
        cursor = self._database["evaluation_sets"].find({}).sort("created_at", -1).limit(100)
        documents = await cursor.to_list(length=100)
        return [EvaluationSet.model_validate(document) for document in documents]

    async def save_training_config(self, config: TrainingConfig) -> TrainingConfig:
        document = learning_document(config)
        document["_id"] = config.training_config_id
        await self._database["training_configs"].insert_one(document)
        return config

    async def create_model_candidate(self, candidate: ModelCandidate) -> ModelCandidate:
        document = learning_document(candidate)
        document["_id"] = candidate.candidate_id
        await self._database["model_candidates"].insert_one(document)
        return candidate

    async def get_model_candidate(self, candidate_id: str) -> ModelCandidate | None:
        document = await self._database["model_candidates"].find_one({"_id": candidate_id})
        return ModelCandidate.model_validate(document) if document else None

    async def list_model_candidates(self) -> list[ModelCandidate]:
        cursor = self._database["model_candidates"].find({}).sort("created_at", -1).limit(100)
        documents = await cursor.to_list(length=100)
        return [ModelCandidate.model_validate(document) for document in documents]

    async def record_deployment_recommendation(
        self, recommendation: DeploymentRecommendation
    ) -> DeploymentRecommendation:
        document = learning_document(recommendation)
        document["_id"] = f"dep_{recommendation.candidate_id}"
        await self._database["deployment_recommendations"].update_one(
            {"_id": document["_id"]}, {"$set": document}, upsert=True
        )
        return recommendation

    async def get_deployment_recommendation(
        self, candidate_id: str
    ) -> DeploymentRecommendation | None:
        document = await self._database["deployment_recommendations"].find_one(
            {"_id": f"dep_{candidate_id}"}
        )
        return DeploymentRecommendation.model_validate(document) if document else None

    async def record_audit_event(self, event_type: str, metadata: Mapping[str, Any]) -> None:
        await self._database["system_audit_events"].insert_one(
            {"event_type": event_type, "metadata": dict(metadata), "created_at": utc_now()}
        )

    async def raw_collection_count(self, collection: str, query: Mapping[str, Any]) -> int:
        cursor = self._database[collection].find(dict(query)).limit(10000)
        documents = await cursor.to_list(length=10000)
        return len(cast(list[Mapping[str, Any]], documents))
