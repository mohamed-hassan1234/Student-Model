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
