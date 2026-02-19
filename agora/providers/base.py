"""Base class for LLM providers."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterator


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        """Generate a completion. Returns the response text."""
        ...

    @abstractmethod
    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        """Stream a completion. Yields text chunks."""
        ...

    @staticmethod
    def resolve(provider: str, model: Optional[str] = None) -> "LLMProvider":
        """Factory: resolve provider name to instance."""
        from agora.providers.anthropic import AnthropicProvider
        from agora.providers.openai import OpenAIProvider
        from agora.providers.gemini import GeminiProvider
        from agora.providers.grok import GrokProvider

        providers = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "grok": GrokProvider,
        }

        name = provider.lower()
        if name not in providers:
            raise ValueError(f"Unknown provider '{provider}'. Available: {', '.join(providers.keys())}")

        return providers[name](model=model)
