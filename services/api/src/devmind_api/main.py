from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devmind_api import __version__
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoManager
from devmind_api.exceptions import register_exception_handlers
from devmind_api.logging import configure_logging
from devmind_api.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from devmind_api.routes.health import router as health_router
from devmind_api.routes.learning import router as learning_router
from devmind_api.routes.technology import router as technology_router

settings = get_settings()
configure_logging(settings.log_level)
mongo_manager = MongoManager(settings)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await mongo_manager.connect()
    yield
    await mongo_manager.close()


def create_app(app_settings: Settings | None = None) -> FastAPI:
    active_settings = app_settings or settings
    app = FastAPI(
        title="DevMind AI API",
        description="DevMind AI local-first API foundation.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["content-type", "authorization", "x-correlation-id", "x-devmind-admin"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(technology_router, prefix="/api/v1")
    app.include_router(learning_router, prefix="/api/v1")
    register_exception_handlers(app)
    return app


app = create_app()
