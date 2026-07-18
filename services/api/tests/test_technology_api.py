from httpx import AsyncClient


async def test_curriculum_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/technology/student/curriculum")

    assert response.status_code == 200
    assert any(topic["topic"] == "react" for topic in response.json()["topics"])


async def test_capabilities_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/technology/student/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["paid_api_required"] is False
    assert body["docker_required"] is False


async def test_register_source_endpoint(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/v1/technology/sources",
        headers=admin_headers,
        json={
            "name": "MDN HTML",
            "description": "Approved HTML docs",
            "original_url": "https://developer.mozilla.org/en-US/docs/Web/HTML",
            "content_type": "text/html",
            "technology_topic": "html",
            "trust_level": "official",
            "license_type": "cc-by-sa",
            "license_review_status": "approved",
            "retrieval_use_permission": "allowed",
            "training_use_permission": "disallowed",
            "human_approval_status": "approved",
            "created_by": "test-admin",
        },
    )

    assert response.status_code == 201
    assert response.json()["source_status"] == "approved"
