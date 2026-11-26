"""Google Gemini provider (Google Gen AI SDK, package ``google-genai``)."""

from __future__ import annotations
import os
import time
from typing import Optional, Iterator

from agora.providers.base import LLMProvider

# Checked 2026-11-26 against Google's model and deprecation pages: gemini-2.0-flash was shut down on
# 2026-06-01; gemini-3.8-flash is the newest Flash marked stable; no Pro model is stable, so `pro` is a preview.
MODELS = {
    "flash": "gemini-3.8-flash",
    "pro": "gemini-3.1-pro-preview",
}

DEFAULT_MODEL = "flash"


class GeminiProvider(LLMProvider):
    """Gemini via the Google Gen AI SDK (the older google-generativeai SDK is deprecated)."""

    def __init__(self, model: Optional[str] = None):
        from google import genai
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise EnvironmentError("GOOGLE_API_KEY not set. Get one at https://aistudio.google.com/apikey")
        self.client = genai.Client(api_key=key)
        model_name = model or DEFAULT_MODEL
        self.model_id = MODELS.get(model_name.lower(), model_name)
        self.display_name = model_name

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        prompt = self._build_prompt(system, messages)
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config={"max_output_tokens": max_tokens},
                )
            except Exception as e:
                if attempt < 2 and self._is_rate_limit(e):
                    time.sleep(2 ** attempt)
                    continue
                raise
            if response.text is None:
                # The new SDK returns None where the old one raised, e.g. for a blocked answer.
                raise ValueError(f"Gemini ({self.model_id}) returned no text (blocked or empty answer)")
            return response.text

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        prompt = self._build_prompt(system, messages)
        response = self.client.models.generate_content_stream(
            model=self.model_id,
            contents=prompt,
            config={"max_output_tokens": max_tokens},
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    @staticmethod
    def _is_rate_limit(error: Exception) -> bool:
        text = str(error).lower()
        return getattr(error, "code", None) == 429 or "rate" in text or "quota" in text

    @staticmethod
    def _build_prompt(system: str, messages: list[dict]) -> str:
        parts = [system, ""]
        for msg in messages:
            role = msg["role"].upper()
            parts.append(f"{role}: {msg['content']}")
        return "\n\n".join(parts)
