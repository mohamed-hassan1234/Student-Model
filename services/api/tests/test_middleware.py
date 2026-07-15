from httpx import AsyncClient


async def test_correlation_id_is_returned(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"x-correlation-id": "test-correlation"})

    assert response.headers["x-correlation-id"] == "test-correlation"


async def test_security_headers_are_set(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/health",
        headers={
            "origin": "http://example.test",
            "access-control-request-method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://example.test"
