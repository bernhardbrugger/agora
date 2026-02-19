"""OpenAI (GPT) provider."""

from __future__ import annotations
import os
import time
from typing import Optional, Iterator

from agora.providers.base import LLMProvider

MODELS = {
    "gpt4": "gpt-4o",
    "gpt4o": "gpt-4o",
    "gpt4o-mini": "gpt-4o-mini",
    "o1": "o1",
    "o3-mini": "o3-mini",
}

DEFAULT_MODEL = "gpt4o"


class OpenAIProvider(LLMProvider):
    """GPT via OpenAI API."""

    def __init__(self, model: Optional[str] = None):
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise EnvironmentError("OPENAI_API_KEY not set. Get one at https://platform.openai.com/api-keys")
        self.client = OpenAI(api_key=key)
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
