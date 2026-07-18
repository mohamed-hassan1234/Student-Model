import pytest
from httpx import AsyncClient

from devmind_shared.time import utc_now

pytestmark = pytest.mark.anyio


async def test_training_auth_blocks_mutations(client: AsyncClient) -> None:
    response = await client.post("/api/v1/technology/training/hardware/inspect")

    assert response.status_code == 401
    assert "Authentication is required" in response.json()["error"]["message"]


async def test_training_hardware_and_base_model_api(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    hardware = await client.get("/api/v1/technology/training/hardware")
    manifest_payload = _manifest_payload()
    validation = await client.post(
        "/api/v1/technology/training/base-models/validate", json=manifest_payload
    )
    created = await client.post(
        "/api/v1/technology/training/base-models",
        headers=admin_headers,
        json=manifest_payload,
    )
    listed = await client.get("/api/v1/technology/training/base-models")

    assert hardware.status_code == 200
    assert hardware.json()["status"] == "not_inspected"
    assert validation.status_code == 200
    assert validation.json()["valid"] is True
    assert created.status_code == 201
    assert listed.status_code == 200
    assert listed.json()["base_model_manifests"][0]["manifest_id"] == "api-manifest"


def _manifest_payload() -> dict[str, object]:
    now = utc_now().isoformat()
    return {
        "manifest_id": "api-manifest",
        "model_identifier": "local/open-weight-test",
        "exact_revision": "0123456789abcdef",
        "model_family": "test-family",
        "parameter_count": "tiny",
        "architecture": "causal_lm",
        "tokenizer_identifier": "local/open-weight-test",
        "tokenizer_revision": "0123456789abcdef",
        "context_length": 2048,
        "license_name": "Apache-2.0",
        "license_reference": "LICENSE",
        "commercial_use_status": "allowed",
        "fine_tuning_permission": "allowed",
        "redistribution_status": "review_required",
        "required_trust_remote_code": False,
        "trust_remote_code_approved": False,
        "expected_memory_gb": 1.0,
        "expected_disk_gb": 1.0,
        "minimum_recommended_hardware": {"ram_gb": 8},
        "human_license_review_status": "approved",
        "approval_status": "approved",
        "created_by": "test-admin",
        "created_at": now,
        "updated_at": now,
    }
