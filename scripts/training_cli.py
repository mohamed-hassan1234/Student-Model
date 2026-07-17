"""Manual Phase 3 training operations.

This command intentionally does not run during application startup, tests, CI,
MongoDB bootstrap, or frontend startup. Real LoRA training requires explicit
operator invocation, approved local assets, and optional training dependencies.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API = "http://127.0.0.1:8000/api/v1/technology/training"


def main() -> int:
    parser = argparse.ArgumentParser(description="DevMind Phase 3 manual training CLI")
    parser.add_argument("--api-base", default=DEFAULT_API)
    parser.add_argument("--admin-token", default="local-admin")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("inspect-hardware")

    validate_manifest = sub.add_parser("validate-base-model-manifest")
    validate_manifest.add_argument("--manifest", required=True)

    register_manifest = sub.add_parser("register-base-model-manifest")
    register_manifest.add_argument("--manifest", required=True)

    validate_dataset = sub.add_parser("validate-dataset")
    validate_dataset.add_argument("--dataset-version", required=True)

    split = sub.add_parser("create-dataset-splits")
    split.add_argument("--dataset-version", required=True)
    split.add_argument("--seed", type=int, default=7)

    baseline = sub.add_parser("run-baseline-evaluation")
    baseline.add_argument("--subject-id", required=True)
    baseline.add_argument("--evaluation-set-version", required=True)
    baseline.add_argument(
        "--unavailable-reason",
        default="No approved inference host configured for baseline evaluation.",
    )

    estimate = sub.add_parser("estimate-training-resources")
    estimate.add_argument("--dataset-version", required=True)

    smoke = sub.add_parser("run-smoke-training")
    smoke.add_argument("--run-id", required=True)

    start_lora = sub.add_parser("start-lora-training")
    start_lora.add_argument("--training-config", required=True)
    start_lora.add_argument("--acknowledge-manual", action="store_true")

    resume = sub.add_parser("resume-run")
    resume.add_argument("--run-id", required=True)
    resume.add_argument("--checkpoint", required=True)

    eval_adapter = sub.add_parser("evaluate-adapter")
    eval_adapter.add_argument("--candidate-id", required=True)
    eval_adapter.add_argument("--evaluation-set-version", required=True)

    compare = sub.add_parser("compare-candidate")
    compare.add_argument("--candidate-id", required=True)
    compare.add_argument("--baseline-evaluation-id", required=True)
    compare.add_argument("--candidate-evaluation-id", required=True)

    register_candidate = sub.add_parser("register-model-candidate")
    register_candidate.add_argument("--candidate-name", required=True)
    register_candidate.add_argument("--training-run-id", required=True)
    register_candidate.add_argument("--baseline-evaluation-id", required=True)
    register_candidate.add_argument("--candidate-evaluation-id", required=True)
    register_candidate.add_argument("--creator", default="local-admin")

    recommendation = sub.add_parser("generate-deployment-recommendation")
    recommendation.add_argument("--candidate-id", required=True)

    archive = sub.add_parser("archive-failed-experiment")
    archive.add_argument("--run-id", required=True)

    args = parser.parse_args()
    return _dispatch(args)


def _dispatch(args: argparse.Namespace) -> int:
    base = args.api_base.rstrip("/")
    admin = {"x-devmind-admin": args.admin_token}
    if args.command == "inspect-hardware":
        _print(_request("POST", f"{base}/hardware/inspect", headers=admin))
    elif args.command == "validate-base-model-manifest":
        _print(_request("POST", f"{base}/base-models/validate", _read_json(args.manifest)))
    elif args.command == "register-base-model-manifest":
        _print(_request("POST", f"{base}/base-models", _read_json(args.manifest), admin))
    elif args.command == "validate-dataset":
        _print(_request("POST", f"{base}/datasets/{args.dataset_version}/validate", headers=admin))
    elif args.command == "create-dataset-splits":
        _print(
            _request(
                "POST",
                f"{base}/datasets/{args.dataset_version}/splits",
                {"seed": args.seed},
                admin,
            )
        )
    elif args.command == "run-baseline-evaluation":
        _print(
            _request(
                "POST",
                f"{base}/evaluations/baseline-unavailable",
                {
                    "subject_id": args.subject_id,
                    "evaluation_set_version": args.evaluation_set_version,
                    "reason": args.unavailable_reason,
                },
                admin,
            )
        )
    elif args.command == "estimate-training-resources":
        _print(_request("POST", f"{base}/datasets/{args.dataset_version}/validate", headers=admin))
    elif args.command == "run-smoke-training":
        _print(_request("POST", f"{base}/runs/{args.run_id}/smoke-train", headers=admin))
    elif args.command == "start-lora-training":
        if not args.acknowledge_manual:
            raise SystemExit("--acknowledge-manual is required for real LoRA training")
        _require_training_dependencies()
        raise SystemExit(
            "Real LoRA backend is enabled only for local operator scripts with approved local "
            "model assets. This command performs dependency gating and does not download models."
        )
    elif args.command == "resume-run":
        _print(
            {
                "manual_resume_check": "Use API run metadata and checkpoint hashes before resume.",
                "run_id": args.run_id,
                "checkpoint": args.checkpoint,
                "automatic_resume": False,
            }
        )
    elif args.command == "evaluate-adapter":
        _print(
            _request(
                "POST",
                f"{base}/evaluations/candidate",
                {
                    "candidate_id": args.candidate_id,
                    "evaluation_set_version": args.evaluation_set_version,
                },
                admin,
            )
        )
    elif args.command == "compare-candidate":
        _print(
            _request(
                "POST",
                f"{base}/candidates/{args.candidate_id}/compare",
                {
                    "baseline_evaluation_id": args.baseline_evaluation_id,
                    "candidate_evaluation_id": args.candidate_evaluation_id,
                },
                admin,
            )
        )
    elif args.command == "register-model-candidate":
        _print(
            _request(
                "POST",
                f"{base}/candidates",
                {
                    "candidate_name": args.candidate_name,
                    "training_run_id": args.training_run_id,
                    "baseline_evaluation_id": args.baseline_evaluation_id,
                    "candidate_evaluation_id": args.candidate_evaluation_id,
                    "creator": args.creator,
                },
                admin,
            )
        )
    elif args.command == "generate-deployment-recommendation":
        _print(
            _request(
                "POST",
                f"{base}/candidates/{args.candidate_id}/recommendation",
                headers=admin,
            )
        )
    elif args.command == "archive-failed-experiment":
        _print(
            {
                "run_id": args.run_id,
                "archive_policy": "mark failed runs archived only after preserving metadata",
                "automatic_deployment": False,
            }
        )
    return 0


def _request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"content-type": "application/json", **(headers or {})}
    request = Request(url, data=body, method=method, headers=request_headers)  # noqa: S310
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - local operator command
            return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))
    except HTTPError as exc:
        message = exc.read().decode("utf-8")
        raise SystemExit(f"API returned {exc.code}: {message}") from exc
    except URLError as exc:
        raise SystemExit(f"Could not reach local DevMind API: {exc.reason}") from exc


def _read_json(path: str) -> dict[str, Any]:
    resolved = Path(path).resolve()
    return cast(dict[str, Any], json.loads(resolved.read_text(encoding="utf-8")))


def _print(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _require_training_dependencies() -> None:
    missing: list[str] = []
    for module in ("torch", "transformers", "datasets", "peft", "accelerate", "safetensors"):
        try:
            __import__(module)
        except Exception:
            missing.append(module)
    if missing:
        raise SystemExit(
            "Missing optional training dependencies: "
            + ", ".join(missing)
            + ". Install the documented training environment manually; no models are downloaded."
        )


if __name__ == "__main__":
    sys.exit(main())
