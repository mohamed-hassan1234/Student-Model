from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, cast

from gridfs import AsyncGridFSBucket


@dataclass(frozen=True)
class StoredFile:
    file_id: str
    filename: str
    content_type: str


class FileStore(Protocol):
    async def put(
        self,
        filename: str,
        content_type: str,
        chunks: AsyncIterator[bytes],
    ) -> StoredFile:
        """Store a file and return metadata safe for API responses."""

    async def delete(self, file_id: str) -> None:
        """Delete a stored file by ID."""


class GridFsFileStore:
    """GridFS adapter boundary for durable uploaded source files."""

    def __init__(self, bucket: AsyncGridFSBucket) -> None:
        self._bucket = bucket

    @classmethod
    def from_database(cls, database: Any) -> "GridFsFileStore":
        return cls(AsyncGridFSBucket(database))

    async def put(
        self,
        filename: str,
        content_type: str,
        chunks: AsyncIterator[bytes],
    ) -> StoredFile:
        data = b""
        async for chunk in chunks:
            data += chunk
        file_id = await self._bucket.upload_from_stream(
            filename,
            data,
            metadata={"content_type": content_type},
        )
        return StoredFile(file_id=str(file_id), filename=filename, content_type=content_type)

    async def delete(self, file_id: str) -> None:
        await self._bucket.delete(cast(Any, file_id))
