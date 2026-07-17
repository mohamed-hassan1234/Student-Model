from collections.abc import Mapping
from typing import Any

from devmind_api.db import MongoDatabase
from devmind_api.technology.training_models import (
    AdapterLoadCheck,
    BaseModelManifest,
    CandidateComparison,
    DatasetSplitManifest,
    DatasetValidationReport,
    HardwareCapabilityReport,
    ModelApproval,
    ModelEvaluation,
    Phase3DeploymentRecommendation,
    Phase3ModelCandidate,
    Phase3TrainingConfig,
    TrainingArtifact,
    TrainingRun,
    training_document,
)
from devmind_shared.time import utc_now


class TrainingRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def create_base_model_manifest(self, manifest: BaseModelManifest) -> BaseModelManifest:
        document = training_document(manifest)
        document["_id"] = manifest.manifest_id
        await self._database["base_model_manifests"].insert_one(document)
        await self.record_audit_event(
            "base_model_manifest_registered",
            {"manifest_id": manifest.manifest_id, "model": manifest.model_identifier},
        )
        return manifest

    async def get_base_model_manifest(self, manifest_id: str) -> BaseModelManifest | None:
        document = await self._database["base_model_manifests"].find_one({"_id": manifest_id})
        return BaseModelManifest.model_validate(document) if document else None

    async def list_base_model_manifests(self) -> list[BaseModelManifest]:
        cursor = self._database["base_model_manifests"].find({}).sort("updated_at", -1).limit(200)
        documents = await cursor.to_list(length=200)
        return [BaseModelManifest.model_validate(document) for document in documents]

    async def update_base_model_manifest(
        self, manifest_id: str, updates: Mapping[str, Any]
    ) -> BaseModelManifest | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["base_model_manifests"].update_one(
            {"_id": manifest_id}, {"$set": payload}
        )
        return await self.get_base_model_manifest(manifest_id)

    async def save_hardware_report(
        self, report: HardwareCapabilityReport
    ) -> HardwareCapabilityReport:
        document = training_document(report)
        document["_id"] = report.report_id
        await self._database["hardware_capability_reports"].insert_one(document)
        return report

    async def latest_hardware_report(self) -> HardwareCapabilityReport | None:
        cursor = (
            self._database["hardware_capability_reports"].find({}).sort("created_at", -1).limit(1)
        )
        documents = await cursor.to_list(length=1)
        return HardwareCapabilityReport.model_validate(documents[0]) if documents else None

    async def save_dataset_validation_report(
        self, report: DatasetValidationReport
    ) -> DatasetValidationReport:
        document = training_document(report)
        document["_id"] = report.report_id
        await self._database["training_dataset_validation_reports"].insert_one(document)
        return report

    async def latest_dataset_validation_report(
        self, dataset_version_id: str
    ) -> DatasetValidationReport | None:
        cursor = (
            self._database["training_dataset_validation_reports"]
            .find({"dataset_version_id": dataset_version_id})
            .sort("created_at", -1)
            .limit(1)
        )
        documents = await cursor.to_list(length=1)
        return DatasetValidationReport.model_validate(documents[0]) if documents else None

    async def create_split_manifest(self, manifest: DatasetSplitManifest) -> DatasetSplitManifest:
        document = training_document(manifest)
        document["_id"] = manifest.split_manifest_id
        await self._database["dataset_split_manifests"].insert_one(document)
        return manifest

    async def get_split_manifest(self, split_manifest_id: str) -> DatasetSplitManifest | None:
        document = await self._database["dataset_split_manifests"].find_one(
            {"_id": split_manifest_id}
        )
        return DatasetSplitManifest.model_validate(document) if document else None

    async def save_phase3_training_config(
        self, config: Phase3TrainingConfig
    ) -> Phase3TrainingConfig:
        document = training_document(config)
        document["_id"] = config.training_config_id
        await self._database["training_configs"].insert_one(document)
        return config

    async def get_phase3_training_config(
        self, training_config_id: str
    ) -> Phase3TrainingConfig | None:
        document = await self._database["training_configs"].find_one({"_id": training_config_id})
        return Phase3TrainingConfig.model_validate(document) if document else None

    async def create_training_run(self, run: TrainingRun) -> TrainingRun:
        document = training_document(run)
        document["_id"] = run.run_id
        await self._database["training_runs"].insert_one(document)
        await self.record_audit_event(
            "training_run_created", {"run_id": run.run_id, "status": run.status.value}
        )
        return run

    async def get_training_run(self, run_id: str) -> TrainingRun | None:
        document = await self._database["training_runs"].find_one({"_id": run_id})
        return TrainingRun.model_validate(document) if document else None

    async def list_training_runs(self, limit: int = 100) -> list[TrainingRun]:
        cursor = self._database["training_runs"].find({}).sort("created_at", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [TrainingRun.model_validate(document) for document in documents]

    async def update_training_run(
        self, run_id: str, updates: Mapping[str, Any]
    ) -> TrainingRun | None:
        payload = dict(updates)
        payload["updated_at"] = utc_now()
        await self._database["training_runs"].update_one({"_id": run_id}, {"$set": payload})
        return await self.get_training_run(run_id)

    async def record_training_artifact(self, artifact: TrainingArtifact) -> TrainingArtifact:
        document = training_document(artifact)
        document["_id"] = artifact.artifact_id
        await self._database["training_artifacts"].insert_one(document)
        return artifact

    async def list_training_artifacts(self, training_run_id: str) -> list[TrainingArtifact]:
        cursor = (
            self._database["training_artifacts"]
            .find({"training_run_id": training_run_id})
            .sort("created_at", 1)
            .limit(500)
        )
        documents = await cursor.to_list(length=500)
        return [TrainingArtifact.model_validate(document) for document in documents]

    async def record_model_evaluation(self, evaluation: ModelEvaluation) -> ModelEvaluation:
        document = training_document(evaluation)
        document["_id"] = evaluation.evaluation_id
        await self._database["model_evaluations"].insert_one(document)
        return evaluation

    async def get_model_evaluation(self, evaluation_id: str) -> ModelEvaluation | None:
        document = await self._database["model_evaluations"].find_one({"_id": evaluation_id})
        return ModelEvaluation.model_validate(document) if document else None

    async def create_model_candidate(self, candidate: Phase3ModelCandidate) -> Phase3ModelCandidate:
        document = training_document(candidate)
        document["_id"] = candidate.candidate_id
        await self._database["model_candidates"].insert_one(document)
        await self.record_audit_event(
            "phase3_model_candidate_registered",
            {
                "candidate_id": candidate.candidate_id,
                "recommendation": candidate.deployment_recommendation.value,
            },
        )
        return candidate

    async def get_phase3_model_candidate(self, candidate_id: str) -> Phase3ModelCandidate | None:
        document = await self._database["model_candidates"].find_one({"_id": candidate_id})
        return Phase3ModelCandidate.model_validate(document) if document else None

    async def list_phase3_model_candidates(self) -> list[Phase3ModelCandidate]:
        cursor = self._database["model_candidates"].find({}).sort("created_at", -1).limit(100)
        documents = await cursor.to_list(length=100)
        candidates: list[Phase3ModelCandidate] = []
        for document in documents:
            if "candidate_name" in document:
                candidates.append(Phase3ModelCandidate.model_validate(document))
        return candidates

    async def record_candidate_comparison(
        self, comparison: CandidateComparison
    ) -> CandidateComparison:
        document = training_document(comparison)
        document["_id"] = comparison.comparison_id
        await self._database["candidate_comparisons"].insert_one(document)
        return comparison

    async def get_candidate_comparison(self, comparison_id: str) -> CandidateComparison | None:
        document = await self._database["candidate_comparisons"].find_one({"_id": comparison_id})
        return CandidateComparison.model_validate(document) if document else None

    async def record_phase3_deployment_recommendation(
        self, recommendation: Phase3DeploymentRecommendation
    ) -> Phase3DeploymentRecommendation:
        document = training_document(recommendation)
        document["_id"] = recommendation.recommendation_id
        await self._database["deployment_recommendations"].insert_one(document)
        return recommendation

    async def record_model_approval(self, approval: ModelApproval) -> ModelApproval:
        document = training_document(approval)
        document["_id"] = approval.approval_id
        await self._database["model_approvals"].insert_one(document)
        await self.record_audit_event(
            "model_approval_action",
            {
                "candidate_id": approval.candidate_id,
                "action": approval.action.value,
                "reviewer": approval.reviewer_id,
            },
        )
        return approval

    async def list_model_approvals(self, candidate_id: str) -> list[ModelApproval]:
        cursor = (
            self._database["model_approvals"]
            .find({"candidate_id": candidate_id})
            .sort("created_at", 1)
            .limit(500)
        )
        documents = await cursor.to_list(length=500)
        return [ModelApproval.model_validate(document) for document in documents]

    async def record_adapter_load_check(self, check: AdapterLoadCheck) -> AdapterLoadCheck:
        document = training_document(check)
        document["_id"] = f"adapter_check_{check.candidate_id}"
        await self._database["adapter_load_checks"].update_one(
            {"_id": document["_id"]}, {"$set": document}, upsert=True
        )
        return check

    async def record_audit_event(self, event_type: str, metadata: Mapping[str, Any]) -> None:
        await self._database["system_audit_events"].insert_one(
            {"event_type": event_type, "metadata": dict(metadata), "created_at": utc_now()}
        )
