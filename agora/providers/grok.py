"""xAI Grok provider (OpenAI-compatible API)."""

from __future__ import annotations
import os
import time
from typing import Optional, Iterator

from agora.providers.base import LLMProvider

MODELS = {
    "grok": "grok-3",
    "grok-mini": "grok-3-mini",
}

DEFAULT_MODEL = "grok"


class GrokProvider(LLMProvider):
    """Grok via xAI API (OpenAI-compatible)."""

    def __init__(self, model: Optional[str] = None):
        from openai import OpenAI
        key = os.environ.get("XAI_API_KEY")
        if not key:
            raise EnvironmentError("XAI_API_KEY not set. Get one at https://console.x.ai/")
        self.client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
        model_name = model or DEFAULT_MODEL
        self.model = MODELS.get(model_name.lower(), model_name)
        self.display_name = model_name

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        oai_messages = [{"role": "system", "content": system}] + messages
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=oai_messages,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < 2 and ("rate" in str(e).lower()):
                    time.sleep(2 ** attempt)
                else:
                    raise

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        oai_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=oai_messages,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
