from abc import ABC, abstractmethod
from src.config import AppConfig
from src.exceptions import ConfigError

from dataclasses import dataclass, field

@dataclass
class LLMResponse:
    text: str
    usage: dict = field(default_factory=dict)

class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> LLMResponse:
        """Generates a completion from the LLM given a prompt."""
        pass

def get_provider(config: AppConfig) -> LLMProvider:
    if config.provider == "lmstudio":
        from .lmstudio_provider import LMStudioProvider
        return LMStudioProvider(config)
    elif config.provider == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(config)
    elif config.provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    elif config.provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(config)
    else:
        raise ConfigError(f"Unknown provider: {config.provider}")
