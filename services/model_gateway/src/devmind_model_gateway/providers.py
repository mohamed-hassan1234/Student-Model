import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    system_prompt: str | None = None
    max_tokens: int = 256


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    text: str
    input_tokens: int
    output_tokens: int


class ModelProvider(Protocol):
    name: str

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Generate a response from a configured model provider."""


class ModelProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class MockProviderConfig:
    model_name: str = "mock-devmind-local"


class MockModelProvider:
    name = "mock"

    def __init__(self, config: MockProviderConfig | None = None) -> None:
        self._config = config or MockProviderConfig()

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        normalized = " ".join(request.prompt.strip().split())
        text = f"[mock:{self._config.model_name}] {normalized or 'empty prompt'}"
        return ProviderResponse(
            provider=self.name,
            model=self._config.model_name,
            text=text,
            input_tokens=len(normalized.split()),
            output_tokens=len(text.split()),
        )


class LocalHttpModelProvider:
    name = "local_http"

    def __init__(
        self, provider_name: str, base_url: str, model_name: str, timeout_seconds: int
    ) -> None:
        self.name = provider_name
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        prompt = request.prompt
        if request.system_prompt:
            prompt = f"{request.system_prompt}\n\n{request.prompt}"
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": request.max_tokens},
        }
        http_request = urllib.request.Request(  # noqa: S310 - local provider URL is explicit configuration.
            f"{self._base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            body = await asyncio.to_thread(self._post_json, http_request)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ModelProviderError("Model provider unavailable") from exc
        text = str(body.get("response") or body.get("text") or "").strip()
        if not text:
            raise ModelProviderError("Model provider returned an empty response")
        return ProviderResponse(
            provider=self.name,
            model=self._model_name,
            text=text,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
        )

    def _post_json(self, http_request: urllib.request.Request) -> dict[str, object]:
        with urllib.request.urlopen(  # noqa: S310 - local provider URL is explicit configuration.
            http_request,
            timeout=self._timeout_seconds,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise ModelProviderError("Model provider returned invalid JSON")
        return body


class OllamaModelProvider(LocalHttpModelProvider):
    def __init__(self, base_url: str, model_name: str, timeout_seconds: int) -> None:
        super().__init__("ollama", base_url, model_name, timeout_seconds)


class LlamaCppHttpModelProvider(LocalHttpModelProvider):
    def __init__(self, base_url: str, model_name: str, timeout_seconds: int) -> None:
        super().__init__("llama_cpp", base_url, model_name, timeout_seconds)


class VllmHttpModelProvider(LocalHttpModelProvider):
    def __init__(self, base_url: str, model_name: str, timeout_seconds: int) -> None:
        super().__init__("vllm", base_url, model_name, timeout_seconds)
