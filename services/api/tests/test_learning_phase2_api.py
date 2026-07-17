import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_learning_admin_placeholder_blocks_mutations(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/technology/learning/cycles",
        json={
            "domain": "Frontend",
            "topic": "React",
            "objectives": ["Explain props"],
            "maximum_examples": 1,
        },
    )

    assert response.status_code == 403
    assert "x-devmind-admin" in response.json()["error"]["message"]


async def test_learning_curriculum_and_cycle_api(client: AsyncClient) -> None:
    curriculum = await client.get("/api/v1/technology/learning/curriculum")
    cycle = await client.post(
        "/api/v1/technology/learning/cycles",
        headers={"x-devmind-admin": "local-admin"},
        json={
            "domain": "Frontend",
            "topic": "React",
            "objectives": ["Explain props"],
            "maximum_examples": 1,
        },
    )

    assert curriculum.status_code == 200
    assert curriculum.json()["topic_scores"]
    assert cycle.status_code == 201
    assert cycle.json()["status"] == "planned"
