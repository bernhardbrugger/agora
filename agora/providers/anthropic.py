"""Anthropic (Claude) provider."""

from __future__ import annotations
import os
import time
from typing import Optional, Iterator

from agora.providers.base import LLMProvider

MODELS = {
    "haiku": "claude-3-5-haiku-20241022",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-0-20250514",
}

DEFAULT_MODEL = "sonnet"


class AnthropicProvider(LLMProvider):
    """Claude via Anthropic API."""

    def __init__(self, model: Optional[str] = None):
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set. Get one at https://console.anthropic.com/")
        self.client = anthropic.Anthropic(api_key=key)
        model_name = model or DEFAULT_MODEL
        self.model = MODELS.get(model_name.lower(), model_name)
        self.display_name = model_name

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                )
                return response.content[0].text
            except Exception as e:
                if attempt < 2 and ("rate" in str(e).lower() or "overloaded" in str(e).lower()):
                    time.sleep(2 ** attempt)
                else:
                    raise

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
