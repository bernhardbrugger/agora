"""Agent class for debate participants."""

from __future__ import annotations

import anthropic


class Agent:
    """A debate participant backed by Claude."""

    def __init__(self, name: str, role: str, color: str = "white", model: str = "claude-opus-4-5-20250514"):
        self.name = name
        self.role = role
        self.color = color
        self.model = model
        self.client = anthropic.Anthropic()

    def respond(self, topic: str, round_num: int, total_rounds: int, history: list[dict]) -> str:
        """Generate a response given the debate history."""
        system_prompt = (
            f"You are '{self.name}' in a structured debate.\n"
            f"Your persona: {self.role}\n\n"
            f"Rules:\n"
            f"- This is round {round_num} of {total_rounds}.\n"
            f"- Be concise but substantive (2-4 paragraphs max).\n"
            f"- You may challenge, agree with, or build on what others said.\n"
            f"- Stay in character at all times.\n"
            f"- Refer to other agents by name when responding to their points."
        )

        messages = self._build_messages(topic, round_num, history)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def _build_messages(self, topic: str, round_num: int, history: list[dict]) -> list[dict]:
        """Build the message list from debate history."""
        messages = []

        if not history:
            messages.append({
                "role": "user",
                "content": f"The debate topic is: \"{topic}\"\n\nYou are the first to speak in round 1. Present your opening position.",
            })
        else:
            transcript = self._format_history(history)
            messages.append({
                "role": "user",
                "content": (
                    f"The debate topic is: \"{topic}\"\n\n"
                    f"Here is the debate so far:\n\n{transcript}\n\n"
                    f"It is now round {round_num}. Respond to the other agents' arguments."
                ),
            })

        return messages

    @staticmethod
    def _format_history(history: list[dict]) -> str:
        """Format debate history into a readable transcript."""
        lines = []
        for entry in history:
            lines.append(f"[Round {entry['round']}] {entry['agent']}:\n{entry['text']}\n")
        return "\n".join(lines)
