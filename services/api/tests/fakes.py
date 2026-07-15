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
        self.documents.append(document)
        return FakeInsertResult()

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None
