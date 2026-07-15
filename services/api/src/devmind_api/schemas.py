from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str = "devmind-api"
    status: str = "healthy"
    version: str


class ReadinessCheck(BaseModel):
    available: bool
    detail: str


class ReadinessResponse(BaseModel):
    service: str = "devmind-api"
    status: str = Field(pattern="^(ready|not_ready)$")
    version: str
    checks: dict[str, ReadinessCheck]
