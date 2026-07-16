from typing import Any


class FakeMongoDatabase:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.commands: list[str | dict[str, Any]] = []
        self.collections: dict[str, FakeCollection] = {}

    async def command(self, command: str | dict[str, Any]) -> dict[str, int]:
        self.commands.append(command)
        if not self.available:
            raise RuntimeError("MongoDB unavailable")
        return {"ok": 1}

    def __getitem__(self, name: str) -> "FakeCollection":
        self.collections.setdefault(name, FakeCollection())
        return self.collections[name]


class FakeInsertResult:
    inserted_id = "fake-id"


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def insert_one(self, document: dict[str, Any]) -> FakeInsertResult:
        stored = dict(document)
        if "_id" not in stored:
            stored["_id"] = f"fake-{len(self.documents) + 1}"
        self.documents.append(stored)
        return FakeInsertResult()

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if _matches(document, query):
                return document
        return None

    def find(self, query: dict[str, Any]) -> "FakeCursor":
        return FakeCursor([document for document in self.documents if _matches(document, query)])

    async def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> None:
        document = await self.find_one(query)
        if document is None:
            if not upsert:
                return
            document = dict(query)
            document.update(update.get("$setOnInsert", {}))
            self.documents.append(document)
        document.update(update.get("$set", {}))


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents
        self._skip = 0
        self._limit: int | None = None

    def sort(self, field: str, direction: int) -> "FakeCursor":
        self._documents = sorted(
            self._documents,
            key=lambda document: document.get(field) or 0,
            reverse=direction < 0,
        )
        return self

    def skip(self, value: int) -> "FakeCursor":
        self._skip = value
        return self

    def limit(self, value: int) -> "FakeCursor":
        self._limit = value
        return self

    async def to_list(self, length: int) -> list[dict[str, Any]]:
        end = self._limit if self._limit is not None else length
        return self._documents[self._skip : self._skip + end]


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, value in query.items():
        if key == "_id" and document.get("_id") != value:
            return False
        if key != "_id" and document.get(key) != value:
            return False
    return True
