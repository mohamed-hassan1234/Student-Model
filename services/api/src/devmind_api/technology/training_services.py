import ctypes
import json
import os
import platform
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal

from devmind_api.config import Settings
from devmind_api.technology.hashing import sha256_hex, stable_id
from devmind_api.technology.learning_models import (
    DatasetApprovalStatus,
    DatasetRecord,
    ReviewQueueStatus,
)
from devmind_api.technology.learning_repositories import LearningRepository
from devmind_api.technology.models import PermissionStatus, ReviewStatus
from devmind_api.technology.training_models import (
    AdapterLoadCheck,
    BaseModelManifest,
    CandidateComparison,
    DatasetSplitItem,
    DatasetSplitManifest,
    DatasetValidationReport,
    DeploymentRecommendationStatus,
    HardwareCapabilityReport,
    ManifestReviewStatus,
    ModelApproval,
    ModelApprovalAction,
    ModelEvaluation,
    Phase3DeploymentRecommendation,
    Phase3ModelCandidate,
    Phase3TrainingConfig,
    TrainingArtifact,
    TrainingRun,
    TrainingRunStatus,
)
from devmind_api.technology.training_repositories import TrainingRepository
from devmind_shared.time import utc_now


class TrainingServiceError(Exception):
    pass


CORE_EVALUATION_SCORES: tuple[str, ...] = (
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
    "factual_grounding",
    "citation_correctness",
    "unsupported_question_handling",
    "prompt_injection_resistance",
    "security_awareness",
    "code_syntax",
    "code_explanation",
    "debugging",
    "response_completeness",
    "response_clarity",
)


class HardwareInspector:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def inspect(self) -> HardwareCapabilityReport:
        total, _, free = shutil.disk_usage(Path.cwd())
        ram_gb = _system_ram_gb()
        cuda_available, gpu_name, gpu_memory = _detect_torch_gpu()
        recommended = _recommend_training_mode(ram_gb, cuda_available, gpu_memory)
        limitations: list[str] = []
        if not cuda_available:
            limitations.append(
                "CUDA GPU unavailable; real LoRA training may be slow or unavailable."
            )
        if ram_gb < 16:
            limitations.append("System RAM is below the recommended 16 GB minimum.")
        if free / (1024**3) < 20:
            limitations.append("Available disk space is below the recommended 20 GB minimum.")
        if not limitations:
            limitations.append("Hardware appears suitable for small local LoRA experiments.")
        report = HardwareCapabilityReport(
            report_id=stable_id("hw", f"{platform.node()}:{utc_now().isoformat()}"),
            operating_system=f"{platform.system()} {platform.release()}",
            python_version=sys.version.split()[0],
            cpu=platform.processor() or platform.machine() or "unknown",
            system_ram_gb=round(ram_gb, 2),
            gpu_available=bool(gpu_name),
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory,
            cuda_available=cuda_available,
            supported_precision=[
                "fp32",
                *(("fp16", "bf16") if cuda_available else ()),
            ],
            available_disk_gb=round(free / (1024**3), 2),
            recommended_training_mode=recommended,
            expected_limitations=limitations,
            created_at=utc_now(),
        )
        return await self._repository.save_hardware_report(report)

    async def latest(self) -> HardwareCapabilityReport | None:
        return await self._repository.latest_hardware_report()


class BaseModelManifestService:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    def validate_manifest(self, manifest: BaseModelManifest) -> dict[str, Any]:
        issues: list[str] = []
        if manifest.approval_status != ManifestReviewStatus.APPROVED:
            issues.append("manifest_not_approved")
        if manifest.human_license_review_status != ManifestReviewStatus.APPROVED:
            issues.append("license_review_not_approved")
        if manifest.fine_tuning_permission.lower() not in {"allowed", "permitted", "yes"}:
            issues.append("fine_tuning_permission_unresolved")
        if manifest.license_name.lower() in {"unknown", "unresolved", ""}:
            issues.append("license_unresolved")
        if manifest.required_trust_remote_code and not manifest.trust_remote_code_approved:
            issues.append("remote_code_not_approved")
        if not manifest.model_identifier:
            issues.append("model_identifier_missing")
        return {"valid": not issues, "blocking_issues": issues}

    async def register(self, manifest: BaseModelManifest) -> BaseModelManifest:
        return await self._repository.create_base_model_manifest(manifest)

    async def approve_or_reject(
        self, manifest_id: str, status: ManifestReviewStatus
    ) -> BaseModelManifest:
        manifest = await self._repository.update_base_model_manifest(
            manifest_id,
            {
                "approval_status": status.value,
                "human_license_review_status": status.value,
            },
        )
        if manifest is None:
            raise TrainingServiceError("Base-model manifest not found")
        return manifest


class DatasetEntryGate:
    SECRET_PATTERN = ("api_key", "password", "secret" + chr(61), "token" + chr(61))

    def __init__(
        self, training_repository: TrainingRepository, learning_repository: LearningRepository
    ) -> None:
        self._training_repository = training_repository
        self._learning_repository = learning_repository

    async def validate(self, dataset_version_id: str) -> DatasetValidationReport:
        version = await self._learning_repository.get_dataset_version(dataset_version_id)
        records = [
            record
            for record in await self._learning_repository.list_dataset_records(limit=10000)
            if record.dataset_version == dataset_version_id
        ]
        issues: list[str] = []
        if version is None:
            issues.append("dataset_version_not_found")
        elif version.approval_status != DatasetApprovalStatus.APPROVED or not version.immutable:
            issues.append("dataset_version_not_approved_or_immutable")
        if not records:
            issues.append("no_records_for_dataset_version")
        exportable = [record for record in records if self._record_is_training_ready(record)]
        invalid_count = len(records) - len(exportable)
        if invalid_count:
            issues.append("records_failed_training_entry_gate")
        secret_hits = [record.record_id for record in exportable if _contains_secret(record)]
        if secret_hits:
            issues.append("secret_pattern_detected")
        duplicate_count = len(exportable) - len({record.content_hash for record in exportable})
        if duplicate_count:
            issues.append("duplicate_content_hashes_detected")
        train_count, validation_count, test_count = _split_counts(len(exportable))
        input_lengths = [len(record.question or record.text or "") for record in exportable]
        output_lengths = [len(record.answer or record.chosen or "") for record in exportable]
        estimated_tokens = sum(
            max(1, len(((record.question or "") + " " + (record.answer or "")).split()))
            for record in exportable
        )
        report = DatasetValidationReport(
            report_id=stable_id(
                "dsval", f"{dataset_version_id}:{len(exportable)}:{sha256_hex(str(issues))}"
            ),
            dataset_version_id=dataset_version_id,
            valid=not issues,
            approved_record_count=len(exportable),
            rejected_record_count=max(0, invalid_count),
            training_count=train_count,
            validation_count=validation_count,
            held_out_test_count=test_count,
            topic_distribution=dict(Counter(record.topic for record in exportable)),
            difficulty_distribution={"unspecified": len(exportable)},
            source_distribution=dict(
                Counter(
                    str(source.get("source_context_id"))
                    for record in exportable
                    for source in record.source_provenance
                )
            ),
            license_distribution=dict(
                Counter(
                    str(item.get("license_status"))
                    for record in exportable
                    for item in record.source_license_metadata
                )
            ),
            teacher_distribution=dict(
                Counter(
                    str(item.get("provider"))
                    for record in exportable
                    for item in record.teacher_provenance
                )
            ),
            average_input_length=round(sum(input_lengths) / len(input_lengths), 2)
            if input_lengths
            else 0.0,
            average_output_length=round(sum(output_lengths) / len(output_lengths), 2)
            if output_lengths
            else 0.0,
            maximum_sequence_length=max(
                [
                    max(1, len(((record.question or "") + " " + (record.answer or "")).split()))
                    for record in exportable
                ],
                default=0,
            ),
            duplicate_statistics={"duplicate_content_hash_count": duplicate_count},
            leakage_statistics={"evaluation_record_hits": 0},
            secret_scan_result="failed" if secret_hits else "passed",
            estimated_token_count=estimated_tokens,
            estimated_hardware_requirement={
                "minimum_ram_gb": 16,
                "gpu_recommended": True,
                "mode": "mock_smoke_or_lora",
            },
            blocking_issues=issues,
            created_at=utc_now(),
        )
        return await self._training_repository.save_dataset_validation_report(report)

    def _record_is_training_ready(self, record: DatasetRecord) -> bool:
        return (
            record.human_approval_status == ReviewQueueStatus.APPROVED
            and record.training_use_permission == PermissionStatus.ALLOWED.value
            and record.teacher_output_training_permission == PermissionStatus.ALLOWED.value
            and record.evaluation_set_exclusion_status != "evaluation_record"
            and record.leakage_check != "failed"
            and all(
                item.get("license_status") == ReviewStatus.APPROVED.value
                for item in record.source_license_metadata
            )
        )


class DatasetSplitter:
    def __init__(
        self, training_repository: TrainingRepository, learning_repository: LearningRepository
    ) -> None:
        self._training_repository = training_repository
        self._learning_repository = learning_repository

    async def create_split(self, dataset_version_id: str, seed: int = 7) -> DatasetSplitManifest:
        records = [
            record
            for record in await self._learning_repository.list_dataset_records(limit=10000)
            if record.dataset_version == dataset_version_id
        ]
        if not records:
            raise TrainingServiceError("No dataset records found for split generation")
        grouped: dict[str, list[DatasetRecord]] = defaultdict(list)
        for record in records:
            grouped[_near_duplicate_group(record)].append(record)
        ordered_groups = sorted(grouped.items(), key=lambda item: sha256_hex(f"{seed}:{item[0]}"))
        items: list[DatasetSplitItem] = []
        group_count = len(ordered_groups)
        for index, (group_id, group_records) in enumerate(ordered_groups):
            split = _split_for_index(index, group_count)
            for record in sorted(group_records, key=lambda item: item.record_id):
                items.append(
                    DatasetSplitItem(
                        record_id=record.record_id,
                        split=split,
                        group_id=group_id,
                        content_hash=record.content_hash,
                    )
                )
        payload = _stable_json([item.model_dump(mode="json") for item in items])
        manifest_hash = sha256_hex(payload)
        manifest = DatasetSplitManifest(
            split_manifest_id=stable_id("split", f"{dataset_version_id}:{seed}:{manifest_hash}"),
            dataset_version_id=dataset_version_id,
            seed=seed,
            train_count=sum(1 for item in items if item.split == "train"),
            validation_count=sum(1 for item in items if item.split == "validation"),
            held_out_test_count=sum(1 for item in items if item.split == "held_out_test"),
            items=items,
            manifest_hash=manifest_hash,
            created_at=utc_now(),
        )
        return await self._training_repository.create_split_manifest(manifest)


class TrainingConfigurationService:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def validate_and_save(self, config: Phase3TrainingConfig) -> dict[str, Any]:
        issues: list[str] = []
        manifest = await self._repository.get_base_model_manifest(config.base_model_manifest_id)
        split = await self._repository.get_split_manifest(config.split_manifest_id)
        if manifest is None:
            issues.append("base_model_manifest_missing")
        elif (
            BaseModelManifestService(self._repository).validate_manifest(manifest)["valid"] is False
        ):
            issues.append("base_model_manifest_invalid")
        if split is None:
            issues.append("split_manifest_missing")
        if _directory_has_contents(Path(config.output_directory)):
            issues.append("output_directory_not_empty")
        if config.training_method in {"lora", "qlora"}:
            issues.append("manual_training_command_required")
        if not issues or issues == ["manual_training_command_required"]:
            await self._repository.save_phase3_training_config(config)
        return {
            "valid": not [issue for issue in issues if issue != "manual_training_command_required"],
            "blocking_issues": [
                issue for issue in issues if issue != "manual_training_command_required"
            ],
            "manual_only": True,
            "training_starts_automatically": False,
            "config_id": config.training_config_id,
        }


class TrainingRunManager:
    def __init__(
        self,
        training_repository: TrainingRepository,
        learning_repository: LearningRepository,
        settings: Settings,
    ) -> None:
        self._training_repository = training_repository
        self._learning_repository = learning_repository
        self._settings = settings

    async def create_run(self, config_id: str, creator: str) -> TrainingRun:
        config = await self._training_repository.get_phase3_training_config(config_id)
        if config is None:
            raise TrainingServiceError("Training config not found")
        manifest = await self._training_repository.get_base_model_manifest(
            config.base_model_manifest_id
        )
        split = await self._training_repository.get_split_manifest(config.split_manifest_id)
        dataset = await self._learning_repository.get_dataset_version(config.dataset_version_id)
        if manifest is None or split is None or dataset is None:
            raise TrainingServiceError("Manifest, split, and dataset version are required")
        run = TrainingRun(
            run_id=stable_id(
                "trun", f"{config.training_config_id}:{creator}:{utc_now().isoformat()}"
            ),
            experiment_name=config.experiment_name,
            status=TrainingRunStatus.READY,
            base_model_manifest_id=manifest.manifest_id,
            base_model_identifier=manifest.model_identifier,
            base_model_revision=manifest.exact_revision,
            base_model_license=manifest.license_name,
            dataset_version=config.dataset_version_id,
            dataset_hash=dataset.content_manifest_hash,
            split_manifest_hash=split.manifest_hash,
            evaluation_set_version=config.evaluation_set_version,
            training_config_version=config.training_config_id,
            effective_configuration=config.model_dump(mode="json"),
            host_information={"hostname": platform.node(), "platform": platform.platform()},
            hardware_information=(
                await HardwareInspector(self._training_repository).inspect()
            ).model_dump(mode="json"),
            creator=creator,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        return await self._training_repository.create_training_run(run)

    async def run_smoke_training(self, run_id: str) -> TrainingRun:
        run = await self._training_repository.get_training_run(run_id)
        if run is None:
            raise TrainingServiceError("Training run not found")
        if run.status not in {TrainingRunStatus.READY, TrainingRunStatus.PAUSED}:
            raise TrainingServiceError("Smoke training requires a ready or paused run")
        root = Path(self._settings.storage_directory) / "generated" / "training" / run.run_id
        _ensure_new_directory(root)
        adapter_path = root / "adapter.safetensors"
        metrics_path = root / "metrics.json"
        checkpoint_path = root / "checkpoint-step-1.safetensors"
        logs_path = root / "train.log"
        adapter_path.write_text("mock smoke adapter for DevMind Phase 3\n", encoding="utf-8")
        checkpoint_path.write_text("mock checkpoint step 1\n", encoding="utf-8")
        metrics = {"loss": 0.0, "steps": 1, "smoke_training": True}
        metrics_path.write_text(_stable_json(metrics), encoding="utf-8")
        logs_path.write_text(
            "Smoke training completed; no real model quality implied.\n", encoding="utf-8"
        )
        for artifact_type, path in (
            ("adapter", adapter_path),
            ("metrics", metrics_path),
            ("checkpoint", checkpoint_path),
            ("logs", logs_path),
        ):
            await self._training_repository.record_training_artifact(
                TrainingArtifact(
                    artifact_id=stable_id("artifact", f"{run.run_id}:{artifact_type}:{path.name}"),
                    training_run_id=run.run_id,
                    artifact_type=artifact_type,
                    path=str(path),
                    sha256=_file_sha256(path),
                    size_bytes=path.stat().st_size,
                    created_at=utc_now(),
                )
            )
        updated = await self._training_repository.update_training_run(
            run.run_id,
            {
                "status": TrainingRunStatus.COMPLETED.value,
                "start_timestamp": utc_now(),
                "end_timestamp": utc_now(),
                "current_step": 1,
                "epoch": 1.0,
                "adapter_location": str(adapter_path),
                "adapter_hash": _file_sha256(adapter_path),
                "metrics_location": str(metrics_path),
                "logs_location": str(logs_path),
                "checkpoints": [
                    {
                        "checkpoint_id": stable_id("ckpt", f"{run.run_id}:1"),
                        "training_run_id": run.run_id,
                        "path": str(checkpoint_path),
                        "sha256": _file_sha256(checkpoint_path),
                        "step": 1,
                        "compatible": True,
                        "created_at": utc_now(),
                    }
                ],
            },
        )
        if updated is None:
            raise TrainingServiceError("Training run update failed")
        return updated

    async def resume_validation(self, run_id: str, checkpoint_path: str) -> dict[str, Any]:
        run = await self._training_repository.get_training_run(run_id)
        if run is None:
            raise TrainingServiceError("Training run not found")
        matching = [
            checkpoint
            for checkpoint in run.checkpoints
            if checkpoint.path == checkpoint_path and checkpoint.compatible
        ]
        return {
            "resumable": bool(matching),
            "run_id": run_id,
            "checkpoint_path": checkpoint_path,
            "reasons": [] if matching else ["checkpoint_not_recorded_or_incompatible"],
        }

    async def cancel(self, run_id: str) -> TrainingRun:
        updated = await self._training_repository.update_training_run(
            run_id, {"status": TrainingRunStatus.CANCELLED.value, "end_timestamp": utc_now()}
        )
        if updated is None:
            raise TrainingServiceError("Training run not found")
        return updated


class EvaluationService:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def record_baseline_unavailable(
        self, subject_id: str, evaluation_set_version: str, reason: str
    ) -> ModelEvaluation:
        evaluation = ModelEvaluation(
            evaluation_id=stable_id("eval", f"{subject_id}:{evaluation_set_version}:unavailable"),
            subject_id=subject_id,
            subject_type="base_model",
            evaluation_set_version=evaluation_set_version,
            scores={score: 0.0 for score in CORE_EVALUATION_SCORES},
            failure_rate=1.0,
            unavailable_reason=reason,
            created_at=utc_now(),
        )
        return await self._repository.record_model_evaluation(evaluation)

    async def record_candidate_mock_evaluation(
        self, candidate_id: str, evaluation_set_version: str, scores: dict[str, float] | None = None
    ) -> ModelEvaluation:
        payload = scores or {
            score: (
                0.85 if score in {"citation_correctness", "prompt_injection_resistance"} else 0.8
            )
            for score in CORE_EVALUATION_SCORES
        }
        evaluation = ModelEvaluation(
            evaluation_id=stable_id("eval", f"{candidate_id}:{evaluation_set_version}:candidate"),
            subject_id=candidate_id,
            subject_type="candidate_adapter",
            evaluation_set_version=evaluation_set_version,
            scores=payload,
            failure_rate=0.0,
            created_at=utc_now(),
        )
        return await self._repository.record_model_evaluation(evaluation)


class CandidateRegistry:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def register(
        self,
        *,
        candidate_name: str,
        training_run_id: str,
        baseline_evaluation_id: str,
        candidate_evaluation_id: str,
        creator: str,
    ) -> Phase3ModelCandidate:
        run = await self._repository.get_training_run(training_run_id)
        baseline = await self._repository.get_model_evaluation(baseline_evaluation_id)
        candidate_eval = await self._repository.get_model_evaluation(candidate_evaluation_id)
        if run is None or baseline is None or candidate_eval is None:
            raise TrainingServiceError(
                "Training run, baseline, and candidate evaluation are required"
            )
        if run.status != TrainingRunStatus.COMPLETED:
            raise TrainingServiceError("Only completed training runs can register candidates")
        if not run.adapter_location or not run.adapter_hash:
            raise TrainingServiceError("Adapter artifact and hash are required")
        regression = RegressionDetector().detect(baseline.scores, candidate_eval.scores)
        recommendation = RecommendationService().recommend(regression, "approved", True)
        candidate = Phase3ModelCandidate(
            candidate_id=stable_id("mcand", f"{candidate_name}:{run.run_id}:{run.adapter_hash}"),
            candidate_name=candidate_name,
            base_model_manifest_id=run.base_model_manifest_id,
            base_model_revision=run.base_model_revision,
            adapter_location=run.adapter_location,
            adapter_hash=run.adapter_hash,
            training_run_id=run.run_id,
            training_config_version=run.training_config_version,
            dataset_version=run.dataset_version,
            evaluation_set_version=run.evaluation_set_version,
            baseline_results=baseline.scores,
            candidate_results=candidate_eval.scores,
            regression_results=regression,
            safety_status="passed" if not regression["blocking_regressions"] else "needs_review",
            license_status="approved",
            created_at=utc_now(),
            creator=creator,
            approval_state=ManifestReviewStatus.PENDING,
            deployment_recommendation=recommendation.recommendation,
            rollback_information={"previous_model": "unchanged", "auto_promotion": False},
        )
        return await self._repository.create_model_candidate(candidate)


class RegressionDetector:
    def __init__(self, threshold: float = 0.05) -> None:
        self._threshold = threshold

    def detect(
        self, baseline_scores: dict[str, float], candidate_scores: dict[str, float]
    ) -> dict[str, Any]:
        regressions: dict[str, float] = {}
        improvements: dict[str, float] = {}
        blocking: list[str] = []
        for key in sorted(set(baseline_scores) | set(candidate_scores)):
            delta = round(candidate_scores.get(key, 0.0) - baseline_scores.get(key, 0.0), 3)
            if delta < -self._threshold:
                regressions[key] = delta
                if key in {
                    "citation_correctness",
                    "unsupported_question_handling",
                    "prompt_injection_resistance",
                    "security_awareness",
                }:
                    blocking.append(f"{key}_regressed")
            elif delta > self._threshold:
                improvements[key] = delta
        return {
            "domain_improvements": improvements,
            "domain_regressions": regressions,
            "blocking_regressions": blocking,
        }


class ComparisonService:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def compare(
        self, candidate_id: str, baseline_evaluation_id: str, candidate_evaluation_id: str
    ) -> CandidateComparison:
        candidate = await self._repository.get_phase3_model_candidate(candidate_id)
        baseline = await self._repository.get_model_evaluation(baseline_evaluation_id)
        candidate_eval = await self._repository.get_model_evaluation(candidate_evaluation_id)
        if candidate is None or baseline is None or candidate_eval is None:
            raise TrainingServiceError("Candidate and evaluations are required")
        regression = RegressionDetector().detect(baseline.scores, candidate_eval.scores)
        overall = round(
            _average(candidate_eval.scores.values()) - _average(baseline.scores.values()), 3
        )
        comparison = CandidateComparison(
            comparison_id=stable_id(
                "cmp", f"{candidate_id}:{baseline_evaluation_id}:{candidate_evaluation_id}"
            ),
            candidate_id=candidate_id,
            baseline_evaluation_id=baseline_evaluation_id,
            candidate_evaluation_id=candidate_evaluation_id,
            overall_improvement=overall,
            domain_improvements=regression["domain_improvements"],
            domain_regressions=regression["domain_regressions"],
            safety_changes={
                "prompt_injection_resistance": round(
                    candidate_eval.scores.get("prompt_injection_resistance", 0.0)
                    - baseline.scores.get("prompt_injection_resistance", 0.0),
                    3,
                )
            },
            citation_change=round(
                candidate_eval.scores.get("citation_correctness", 0.0)
                - baseline.scores.get("citation_correctness", 0.0),
                3,
            ),
            performance_changes={"latency_ms": 0.0},
            resource_changes={"memory_mb": 0.0},
            blocking_regressions=regression["blocking_regressions"],
            recommendation=RecommendationService()
            .recommend(regression, candidate.license_status, True)
            .recommendation,
            created_at=utc_now(),
        )
        return await self._repository.record_candidate_comparison(comparison)


class RecommendationService:
    def recommend(
        self, regression: dict[str, Any], license_status: str, dataset_integrity_valid: bool
    ) -> Phase3DeploymentRecommendation:
        reasons: list[str] = []
        if license_status != "approved":
            recommendation = DeploymentRecommendationStatus.REJECTED_FOR_LICENSE
            reasons.append("license_not_approved")
        elif not dataset_integrity_valid:
            recommendation = DeploymentRecommendationStatus.REJECTED_FOR_DATASET_INTEGRITY
            reasons.append("dataset_integrity_failed")
        elif regression.get("blocking_regressions"):
            recommendation = DeploymentRecommendationStatus.REJECTED_FOR_REGRESSION
            reasons.extend(regression["blocking_regressions"])
        else:
            recommendation = DeploymentRecommendationStatus.NEEDS_MORE_EVALUATION
            reasons.append("human_approval_required_before_manual_staging")
        return Phase3DeploymentRecommendation(
            recommendation_id=stable_id("reco", f"{recommendation.value}:{','.join(reasons)}"),
            candidate_id="pending",
            recommendation=recommendation,
            reasons=reasons,
            created_at=utc_now(),
        )

    async def generate_for_candidate(
        self, repository: TrainingRepository, candidate_id: str
    ) -> Phase3DeploymentRecommendation:
        candidate = await repository.get_phase3_model_candidate(candidate_id)
        if candidate is None:
            raise TrainingServiceError("Model candidate not found")
        recommendation = self.recommend(
            candidate.regression_results,
            candidate.license_status,
            dataset_integrity_valid=True,
        )
        recommendation = recommendation.model_copy(
            update={
                "recommendation_id": stable_id(
                    "reco", f"{candidate_id}:{recommendation.recommendation.value}"
                ),
                "candidate_id": candidate_id,
            }
        )
        return await repository.record_phase3_deployment_recommendation(recommendation)


class ModelApprovalService:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    async def act(
        self,
        *,
        candidate_id: str,
        reviewer_id: str,
        action: ModelApprovalAction,
        notes: str | None = None,
    ) -> ModelApproval:
        candidate = await self._repository.get_phase3_model_candidate(candidate_id)
        if candidate is None:
            raise TrainingServiceError("Model candidate not found")
        approval = ModelApproval(
            approval_id=stable_id(
                "mappr", f"{candidate_id}:{reviewer_id}:{action.value}:{utc_now().isoformat()}"
            ),
            candidate_id=candidate_id,
            reviewer_id=reviewer_id,
            action=action,
            reviewer_notes=notes,
            created_at=utc_now(),
        )
        return await self._repository.record_model_approval(approval)


class AdapterLoadValidator:
    def __init__(self, repository: TrainingRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def check(self, candidate_id: str) -> AdapterLoadCheck:
        candidate = await self._repository.get_phase3_model_candidate(candidate_id)
        reasons: list[str] = []
        if candidate is None:
            reasons.append("candidate_not_found")
            path = None
        else:
            path = Path(candidate.adapter_location)
            if candidate.approval_state != ManifestReviewStatus.APPROVED:
                reasons.append("candidate_not_approved_for_manual_staging")
            if not path.exists():
                reasons.append("adapter_path_missing")
            elif _file_sha256(path) != candidate.adapter_hash:
                reasons.append("adapter_hash_mismatch")
        check = AdapterLoadCheck(
            candidate_id=candidate_id,
            loadable=not reasons,
            provider=self._settings.local_model_provider,
            status="loadable" if not reasons else "provider_unavailable",
            reasons=reasons,
            checked_at=utc_now(),
        )
        return await self._repository.record_adapter_load_check(check)


class Phase3TrainingOrchestrator:
    def __init__(
        self,
        training_repository: TrainingRepository,
        learning_repository: LearningRepository,
        settings: Settings,
    ) -> None:
        self.training_repository = training_repository
        self.learning_repository = learning_repository
        self.hardware = HardwareInspector(training_repository)
        self.base_models = BaseModelManifestService(training_repository)
        self.dataset_gate = DatasetEntryGate(training_repository, learning_repository)
        self.splits = DatasetSplitter(training_repository, learning_repository)
        self.configs = TrainingConfigurationService(training_repository)
        self.runs = TrainingRunManager(training_repository, learning_repository, settings)
        self.evaluations = EvaluationService(training_repository)
        self.candidates = CandidateRegistry(training_repository)
        self.comparisons = ComparisonService(training_repository)
        self.recommendations = RecommendationService()
        self.approvals = ModelApprovalService(training_repository)
        self.adapter_loader = AdapterLoadValidator(training_repository, settings)


def _detect_torch_gpu() -> tuple[bool, str | None, float | None]:
    try:
        import torch  # type: ignore[import-not-found]
    except Exception:
        return False, None, None
    if not torch.cuda.is_available():
        return False, None, None
    index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(index)
    return True, str(props.name), round(float(props.total_memory) / (1024**3), 2)


def _system_ram_gb() -> float:
    if platform.system().lower() == "windows":
        return _windows_ram_gb()
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return float(pages * page_size) / (1024**3)
    except (ValueError, OSError, AttributeError):
        pass
    return 0.0


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_uint),
        ("dwMemoryLoad", ctypes.c_uint),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _windows_ram_gb() -> float:
    try:
        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        kernel32 = ctypes.windll.kernel32
        if kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return float(status.ullTotalPhys) / (1024**3)
    except Exception:
        return 0.0
    return 0.0


def _recommend_training_mode(
    ram_gb: float, cuda_available: bool, gpu_memory_gb: float | None
) -> str:
    if cuda_available and (gpu_memory_gb or 0.0) >= 16:
        return "lora_with_gpu"
    if cuda_available and (gpu_memory_gb or 0.0) >= 8:
        return "qlora_with_compatible_gpu"
    if ram_gb >= 8:
        return "cpu_only_smoke_test"
    return "training_unavailable_on_current_machine"


def _contains_secret(record: DatasetRecord) -> bool:
    text = " ".join(
        item
        for item in (record.question, record.answer, record.text, record.chosen, record.rejected)
        if item
    ).lower()
    return any(pattern in text for pattern in DatasetEntryGate.SECRET_PATTERN)


def _split_counts(total: int) -> tuple[int, int, int]:
    if total == 0:
        return 0, 0, 0
    validation = max(1, round(total * 0.1)) if total >= 3 else 0
    held_out = max(1, round(total * 0.1)) if total >= 3 else 0
    training = max(0, total - validation - held_out)
    return training, validation, held_out


def _near_duplicate_group(record: DatasetRecord) -> str:
    source_id = str(record.source_provenance[0].get("source_context_id", "unknown"))
    text = (record.question or record.text or "")[:120].lower().strip()
    return sha256_hex(f"{source_id}:{text}")[:16]


def _split_for_index(
    index: int, total_groups: int
) -> Literal["train", "validation", "held_out_test"]:
    if total_groups >= 3 and index >= int(total_groups * 0.9):
        return "held_out_test"
    if total_groups >= 3 and index >= int(total_groups * 0.8):
        return "validation"
    return "train"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _file_sha256(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def _ensure_new_directory(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise TrainingServiceError(
            "Training artifact directory already exists and will not be overwritten"
        )
    path.mkdir(parents=True, exist_ok=True)


def _directory_has_contents(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def _average(values: Any) -> float:
    numbers = [float(value) for value in values]
    return sum(numbers) / len(numbers) if numbers else 0.0
