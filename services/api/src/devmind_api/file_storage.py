from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


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
    """GridFS adapter boundary for future durable file storage.

    Phase 0 defines the boundary only; upload workflows are intentionally out of scope.
    """

    def __init__(self, bucket: object) -> None:
        self._bucket = bucket

    async def put(
        self,
        filename: str,
        content_type: str,
        chunks: AsyncIterator[bytes],
    ) -> StoredFile:
        del filename, content_type, chunks
        raise NotImplementedError("GridFS uploads are not implemented in Phase 0")

    async def delete(self, file_id: str) -> None:
        del file_id
        raise NotImplementedError("GridFS deletion is not implemented in Phase 0")
