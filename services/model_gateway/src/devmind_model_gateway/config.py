from dataclasses import dataclass
from enum import StrEnum


class ProviderKind(StrEnum):
    MOCK = "mock"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    APPROVED_EXTERNAL = "approved_external"


@dataclass(frozen=True)
class ProviderConfig:
    provider: ProviderKind
    base_url: str | None
    model_name: str
    secret_name: str | None = None
