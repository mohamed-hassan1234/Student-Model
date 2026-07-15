from collections.abc import Mapping
from typing import Any, Protocol, cast, runtime_checkable

from pymongo import AsyncMongoClient

from devmind_api.config import Settings


@runtime_checkable
class MongoDatabase(Protocol):
    async def command(self, command: str | Mapping[str, Any]) -> Mapping[str, Any]:
        """Run a MongoDB command."""

    def __getitem__(self, name: str) -> Any:
        """Return a collection handle."""


class MongoManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncMongoClient[Any] | None = None

    async def connect(self) -> None:
        if self._client is None:
            self._client = AsyncMongoClient(
                self._settings.mongodb_uri,
                serverSelectionTimeoutMS=self._settings.mongodb_connect_timeout_ms,
                connectTimeoutMS=self._settings.mongodb_connect_timeout_ms,
            )
            await self.ping()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def database(self) -> MongoDatabase:
        if self._client is None:
            raise RuntimeError("MongoDB client is not connected")
        return cast(MongoDatabase, self._client[self._settings.mongodb_database])

    async def ping(self) -> bool:
        if self._client is None:
            raise RuntimeError("MongoDB client is not connected")
        result = await self._client.admin.command("ping")
        return result.get("ok") == 1


async def get_database() -> MongoDatabase:
    from devmind_api.main import mongo_manager

    return mongo_manager.database
