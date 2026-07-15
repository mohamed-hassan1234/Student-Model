from collections.abc import Mapping
from typing import Any, cast

from devmind_api.db import MongoDatabase


class SystemRepository:
    def __init__(self, database: MongoDatabase) -> None:
        self._database = database

    async def record_audit_event(self, event: Mapping[str, Any]) -> str:
        result = await self._database["system_audit_events"].insert_one(dict(event))
        return str(result.inserted_id)

    async def get_schema_version(self, component: str) -> Mapping[str, Any] | None:
        result = await self._database["system_schema_versions"].find_one({"component": component})
        return cast(Mapping[str, Any] | None, result)
