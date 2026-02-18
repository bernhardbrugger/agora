"""Moderator agent that synthesizes the debate."""

from __future__ import annotations

import time
import anthropic

from agora.agent import resolve_model


class Moderator:
    """Neutral moderator that analyzes the full debate and provides a synthesis."""

    def __init__(self, model: str = "sonnet"):
        self.model = resolve_model(model)
        self.client = anthropic.Anthropic()

    def synthesize(self, topic: str, history: list[dict], agent_names: list[str]) -> str:
        """Read the full debate transcript and produce a synthesis."""
        transcript = self._format_transcript(history)

        system_prompt = (
            "You are a neutral, highly analytical debate moderator.\n"
            "Your job is to synthesize a structured debate between multiple agents.\n"
            "Be fair, balanced, and insightful. Do not take sides unless the evidence clearly warrants it."
        )

        user_prompt = (
            f"The debate topic was: \"{topic}\"\n"
            f"Participants: {', '.join(agent_names)}\n\n"
            f"Full transcript:\n\n{transcript}\n\n"
            f"Please provide your synthesis in EXACTLY this format:\n\n"
            f"## Key Arguments FOR\n"
            f"- (list the strongest arguments in favor)\n\n"
            f"## Key Arguments AGAINST\n"
            f"- (list the strongest arguments against)\n\n"
            f"## Surprising Insights\n"
            f"- (list unexpected points or novel perspectives that emerged)\n\n"
            f"## Final Recommendation\n"
            f"(your recommendation with clear reasoning)\n\n"
            f"## Confidence Score\n"
            f"(a single number 0-100 indicating how confident you are in this recommendation, "
            f"followed by a brief justification)"
        )

        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text
            except anthropic.RateLimitError:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except anthropic.APIError:
                if attempt < 2:
                    time.sleep(1)
                else:
                    raise

    @staticmethod
    def _format_transcript(history: list[dict]) -> str:
        lines = []
        for entry in history:
            lines.append(f"[Round {entry['round']}] {entry['agent']}:\n{entry['text']}\n")
        return "\n".join(lines)
