"""Offline provider with canned, deterministic replies (``agora run --dry-run``).

It needs no API key and makes no network request. It lets you see the whole
debate flow (phases, moderator, consensus meter, report) for free, and it is what
the tests and the README examples use. The text is placeholder text, not a debate.
"""

from __future__ import annotations

import re
from typing import Iterator, Optional

from agora.providers.base import LLMProvider

_NAME_RE = re.compile(r"You are '(.+?)' participating")
_PHASE_RE = re.compile(r"CURRENT PHASE: (.+?) \(Round (\d+) of (\d+)\)")
_TOPIC_RE = re.compile(r'(?:debate topic is|Debate topic): "([^"]*)"')
_CARD_RE = re.compile(r"Evidence cards (E\d+)")  # the first card id from the speaker's rules

# Speakers alternate between the two stances in the order they first speak; every
# speaker ends on "support" in the closing round.
_STANCES = ("support", "oppose")


class DryRunProvider(LLMProvider):
    """Returns canned replies built from the prompt; never calls a model."""

    def __init__(self, model: Optional[str] = None):
        self.model = "canned"
        self.display_name = "canned"
        self._speakers: dict[str, int] = {}

    def _stance(self, name: str, phase_label: str) -> str:
        if phase_label == "Closing Argument":
            return "support"
        index = self._speakers.setdefault(name, len(self._speakers))
        return _STANCES[index % len(_STANCES)]

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        user = messages[-1]["content"] if messages else ""
        topic_match = _TOPIC_RE.search(user)
        topic = topic_match.group(1) if topic_match else "the topic"

        if system.startswith("You are a Socratic debate moderator"):
            return (
                "[dry run] Name one concrete case where your position fails, "
                f'and say what that means for "{topic}".'
            )
        if system.startswith("You are a world-class debate analyst"):
            outline = user.split("EXACTLY THIS FORMAT", 1)[-1]
            if "## The Real Crux" in outline:
                return _SYNTHESIS.format(topic=topic)
            # a debate format's own outline (e.g. the committee memo): same headings, placeholder text
            headings = re.findall(r"^## (.+)$", outline, re.M)
            body = "\n\n".join(f"## {h.strip()}\nPlaceholder." for h in headings)
            return f'[dry run] Canned synthesis for "{topic}"; no model was called.\n\n{body}'

        name_match = _NAME_RE.search(system)
        phase_match = _PHASE_RE.search(system)
        name = name_match.group(1) if name_match else "Agent"
        label = phase_match.group(1) if phase_match else "Rebuttal"
        round_num = phase_match.group(2) if phase_match else "?"
        stance = self._stance(name, label)
        steelman = (
            "STEELMAN: [dry run] the other side's strongest argument goes here.\n"
            if "STEELMAN: " in system else ""
        )
        crux = "CRUX: [dry run] the question that would change my mind goes here.\n" if "CRUX: " in system else ""
        card = _CARD_RE.search(system)
        cites = (
            f"[dry run] A real speaker would argue from the evidence here [source: {card.group(1)}].\n\n"
            if card else ""
        )
        return (
            f"[dry run] {name}, {label.lower()} in round {round_num}. "
            f'This is canned text: no model was called for "{topic}".\n\n'
            f"{cites}{steelman}{crux}POSITION: I {stance} it."
        )

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Iterator[str]:
        text = self.complete(system, messages, max_tokens)
        for word in re.findall(r"\S+\s*", text):
            yield word


_SYNTHESIS = """[dry run] Canned synthesis for "{topic}"; no model was called.

## The Real Crux
Placeholder: a real run names the underlying disagreement here.

## Strongest Arguments FOR
- Placeholder.

## Strongest Arguments AGAINST
- Placeholder.

## Position Evolution
Placeholder: every dry-run speaker ends on "support".

## Surprising Insights
- Placeholder.

## Common Ground
Placeholder.

## Unresolved Cruxes
- Placeholder.

## Final Recommendation
None: this was a dry run.

## Confidence Score
0 - canned text, nothing was decided."""
