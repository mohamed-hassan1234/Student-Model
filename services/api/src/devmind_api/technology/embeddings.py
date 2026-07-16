import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from devmind_api.technology.hashing import sha256_hex


class EmbeddingProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingRequest:
    text: str


@dataclass(frozen=True)
class EmbeddingResult:
    provider: str
    model: str
    dimensions: int
    vector: list[float]
    model_version: str | None = None


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Return an embedding vector for text."""


class MockEmbeddingProvider:
    provider_name = "mock"

    def __init__(self, model_name: str = "mock-embedding", dimensions: int = 16) -> None:
        self.model_name = model_name
        self.dimensions = dimensions

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        digest = sha256_hex(request.text)
        values: list[float] = []
        for index in range(self.dimensions):
            start = (index * 2) % len(digest)
            raw = int(digest[start : start + 2], 16)
            values.append((raw / 127.5) - 1.0)
        return EmbeddingResult(
            provider=self.provider_name,
            model=self.model_name,
            dimensions=self.dimensions,
            vector=_normalize(values),
        )


class OllamaEmbeddingProvider:
    provider_name = "ollama"

    def __init__(
        self, base_url: str, model_name: str, dimensions: int, timeout_seconds: int
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        payload = json.dumps({"model": self.model_name, "prompt": request.text}).encode("utf-8")
        http_request = urllib.request.Request(  # noqa: S310 - local provider URL is explicit configuration.
            f"{self.base_url}/api/embeddings",
            data=payload,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            body = await asyncio.to_thread(self._post_json, http_request)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EmbeddingProviderError("Embedding provider unavailable") from exc
        raw_embedding = body.get("embedding")
        if not isinstance(raw_embedding, list):
            raise EmbeddingProviderError("Embedding provider returned invalid embedding")
        vector = [float(value) for value in raw_embedding]
        if len(vector) != self.dimensions:
            raise EmbeddingProviderError("Embedding dimension mismatch")
        return EmbeddingResult(
            provider=self.provider_name,
            model=self.model_name,
            dimensions=len(vector),
            vector=vector,
        )

    def _post_json(self, http_request: urllib.request.Request) -> dict[str, object]:
        with urllib.request.urlopen(  # noqa: S310 - local provider URL is explicit configuration.
            http_request,
            timeout=self.timeout_seconds,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise EmbeddingProviderError("Embedding provider returned invalid JSON")
        return body


class LocalHttpEmbeddingProvider(OllamaEmbeddingProvider):
    provider_name = "local_http"


def _normalize(values: list[float]) -> list[float]:
    magnitude = sum(value * value for value in values) ** 0.5
    if magnitude == 0:
        return values
    return [value / magnitude for value in values]
