"""Agent class for debate participants."""

from __future__ import annotations

from typing import Optional, Iterator

from agora.providers.base import LLMProvider


class Agent:
    """A debate participant backed by an LLM."""

    def __init__(self, name: str, role: str, color: str = "white", provider: Optional[LLMProvider] = None):
        self.name = name
        self.role = role
        self.color = color
        self.provider = provider or LLMProvider.resolve("anthropic")

    def respond(self, topic: str, round_num: int, total_rounds: int, history: list[dict]) -> str:
        """Generate a response given the debate history."""
        system = self._system_prompt(round_num, total_rounds)
        messages = self._build_messages(topic, round_num, history)
        return self.provider.complete(system, messages)

    def respond_stream(self, topic: str, round_num: int, total_rounds: int, history: list[dict]) -> Iterator[str]:
        """Generate a streaming response. Yields text chunks."""
        system = self._system_prompt(round_num, total_rounds)
        messages = self._build_messages(topic, round_num, history)
        return self.provider.stream(system, messages)

    def _system_prompt(self, round_num: int, total_rounds: int) -> str:
        return (
            f"You are '{self.name}' in a structured debate.\n"
            f"Your persona: {self.role}\n\n"
            f"Rules:\n"
            f"- This is round {round_num} of {total_rounds}.\n"
            f"- Be concise but substantive (2-4 paragraphs max).\n"
            f"- You may challenge, agree with, or build on what others said.\n"
            f"- Stay in character at all times.\n"
            f"- Refer to other agents by name when responding to their points."
        )

    def _build_messages(self, topic: str, round_num: int, history: list[dict]) -> list[dict]:
        """Build the message list from debate history."""
        if not history:
            return [{
                "role": "user",
                "content": f"The debate topic is: \"{topic}\"\n\nYou are the first to speak in round 1. Present your opening position.",
            }]

        transcript = self._format_history(history)
        return [{
            "role": "user",
            "content": (
                f"The debate topic is: \"{topic}\"\n\n"
                f"Here is the debate so far:\n\n{transcript}\n\n"
                f"It is now round {round_num}. Respond to the other agents' arguments."
            ),
        }]

    @staticmethod
    def _format_history(history: list[dict]) -> str:
        lines = []
        for entry in history:
            lines.append(f"[Round {entry['round']}] {entry['agent']}:\n{entry['text']}\n")
        return "\n".join(lines)
