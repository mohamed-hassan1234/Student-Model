from typing import Annotated

from fastapi import APIRouter, Depends

from devmind_api import __version__
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoDatabase, get_database
from devmind_api.schemas import HealthResponse, ReadinessCheck, ReadinessResponse

router = APIRouter(tags=["system"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    settings: SettingsDep,
    database: DatabaseDep,
) -> ReadinessResponse:
    checks = {
        "api": ReadinessCheck(available=True, detail="process available"),
        "configuration": ReadinessCheck(
            available=bool(settings.mongodb_database and settings.mongodb_uri),
            detail="required configuration present",
        ),
        "mongodb": ReadinessCheck(available=False, detail="ping not attempted"),
    }
    try:
        result = await database.command("ping")
        checks["mongodb"] = ReadinessCheck(
            available=result.get("ok") == 1,
            detail="ping succeeded" if result.get("ok") == 1 else "ping returned unexpected result",
        )
    except Exception:
        checks["mongodb"] = ReadinessCheck(available=False, detail="ping failed")

    status = "ready" if all(check.available for check in checks.values()) else "not_ready"
    return ReadinessResponse(version=__version__, status=status, checks=checks)
