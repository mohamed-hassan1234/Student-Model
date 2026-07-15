from httpx import AsyncClient


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "devmind-api",
        "status": "healthy",
        "version": "0.1.0",
    }


async def test_ready_endpoint_with_mongodb_available(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["mongodb"]["available"] is True


async def test_ready_endpoint_with_mongodb_unavailable(app, test_settings) -> None:  # type: ignore[no-untyped-def]
    from fakes import FakeMongoDatabase
    from httpx import ASGITransport, AsyncClient

    from devmind_api.config import get_settings
    from devmind_api.db import get_database

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_database] = lambda: FakeMongoDatabase(available=False)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["mongodb"]["available"] is False
