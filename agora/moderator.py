"""Moderator agent that synthesizes the debate."""

from __future__ import annotations

import anthropic


class Moderator:
    """Neutral moderator that analyzes the full debate and provides a synthesis."""

    def __init__(self, model: str = "claude-opus-4-5-20250514"):
        self.model = model
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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    @staticmethod
    def _format_transcript(history: list[dict]) -> str:
        lines = []
        for entry in history:
            lines.append(f"[Round {entry['round']}] {entry['agent']}:\n{entry['text']}\n")
        return "\n".join(lines)
