from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from devmind_api.exceptions import DevMindError, register_exception_handlers


async def test_central_exception_handler_returns_safe_error() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise DevMindError("safe failure")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/boom")

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "safe failure"
