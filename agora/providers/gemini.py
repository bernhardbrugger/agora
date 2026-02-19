"""Google Gemini provider."""

from __future__ import annotations
import os
import time
from typing import Optional, Iterator

from agora.providers.base import LLMProvider

MODELS = {
    "flash": "gemini-2.0-flash",
    "pro": "gemini-2.0-pro",
    "thinking": "gemini-2.0-flash-thinking",
}

DEFAULT_MODEL = "flash"


class GeminiProvider(LLMProvider):
    """Gemini via Google Generative AI API."""

    def __init__(self, model: Optional[str] = None):
        import google.generativeai as genai
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise EnvironmentError("GOOGLE_API_KEY not set. Get one at https://aistudio.google.com/apikey")
        genai.configure(api_key=key)
        model_name = model or DEFAULT_MODEL
        self.model_id = MODELS.get(model_name.lower(), model_name)
        self.model = genai.GenerativeModel(self.model_id)
        self.display_name = model_name

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        prompt = self._build_prompt(system, messages)
        for attempt in range(3):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"max_output_tokens": max_tokens},
                )
                return response.text
            except Exception as e:
                if attempt < 2 and ("rate" in str(e).lower() or "quota" in str(e).lower()):
                    time.sleep(2 ** attempt)
                else:
                    raise

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        prompt = self._build_prompt(system, messages)
        response = self.model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens},
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    @staticmethod
    def _build_prompt(system: str, messages: list[dict]) -> str:
        parts = [system, ""]
        for msg in messages:
            role = msg["role"].upper()
            parts.append(f"{role}: {msg['content']}")
        return "\n\n".join(parts)
