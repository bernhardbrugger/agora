"""Agent class for debate participants."""

from __future__ import annotations

from typing import Iterator, Optional

from agora.providers.base import LLMProvider

# Debate phases with phase-specific argumentation instructions
PHASE_INSTRUCTIONS: dict[str, str] = {
    "opening": (
        "This is your OPENING STATEMENT.\n"
        "• Establish your core thesis in the first sentence.\n"
        "• Lay out your 2–3 strongest arguments with supporting reasoning.\n"
        "• State clearly where you stand on the topic.\n"
        "• Do NOT yet respond to others — this is your independent opening position."
    ),
    "rebuttal": (
        "This is a REBUTTAL round.\n"
        "• Quote or directly paraphrase the single strongest argument made against your view.\n"
        "• Rebut it specifically — not in general terms.\n"
        "• Advance your position with a new argument, angle, or evidence.\n"
        "• Acknowledge any valid points from others — intellectual honesty is required.\n"
        "• If you have been partially convinced of something, say so explicitly."
    ),
    "cross_examination": (
        "This is a CROSS-EXAMINATION round.\n"
        "• Pose one sharp, specific question directly to another debater — name them.\n"
        "• The question must target an inconsistency, undefended assumption, or gap in their argument.\n"
        "• Defend your own position against the strongest attack it has received.\n"
        "• If a prior argument has genuinely shifted your thinking, acknowledge the shift."
    ),
    "closing": (
        "This is your CLOSING STATEMENT.\n"
        "• Summarise your core argument in 1–2 sentences.\n"
        "• Name the single strongest opposing point — and either concede or refute it clearly.\n"
        "• State your FINAL POSITION — it may have evolved from your opening.\n"
        "• Identify at least one specific area of potential common ground or resolution.\n"
        "• Be definitive. Vague conclusions are a sign of weak reasoning."
    ),
}

PHASE_LABELS: dict[str, str] = {
    "opening": "Opening Statement",
    "rebuttal": "Rebuttal",
    "cross_examination": "Cross-Examination",
    "closing": "Closing Argument",
}


def format_history(history: list[dict]) -> str:
    """Format debate history into a structured transcript."""
    if not history:
        return ""
    lines: list[str] = []
    current_round: Optional[int] = None
    for entry in history:
        if entry["round"] != current_round:
            current_round = entry["round"]
            phase = entry.get("phase", "")
            phase_label = PHASE_LABELS.get(phase, phase.upper()) if phase else ""
            header = f"── Round {current_round}"
            if phase_label:
                header += f" · {phase_label}"
            header += " ──"
            lines.append(f"\n{header}")
        lines.append(f"\n[{entry['agent']}]:\n{entry['text']}\n")
    return "\n".join(lines)


class Agent:
    """A debate participant backed by an LLM provider."""

    def __init__(
        self,
        name: str,
        role: str,
        color: str = "white",
        provider: Optional[LLMProvider] = None,
    ):
        self.name = name
        self.role = role
        self.color = color
        self.provider = provider or LLMProvider.resolve("anthropic")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def respond(
        self,
        topic: str,
        round_num: int,
        total_rounds: int,
        history: list[dict],
        phase: str = "rebuttal",
        moderator_prompt: Optional[str] = None,
    ) -> str:
        """Generate a non-streaming response."""
        system = self._build_system_prompt(round_num, total_rounds, phase)
        messages = self._build_messages(topic, round_num, history, moderator_prompt)
        return self.provider.complete(system, messages, max_tokens=1500)

    def respond_stream(
        self,
        topic: str,
        round_num: int,
        total_rounds: int,
        history: list[dict],
        phase: str = "rebuttal",
        moderator_prompt: Optional[str] = None,
    ) -> Iterator[str]:
        """Generate a streaming response, yielding text chunks."""
        system = self._build_system_prompt(round_num, total_rounds, phase)
        messages = self._build_messages(topic, round_num, history, moderator_prompt)
        return self.provider.stream(system, messages, max_tokens=1500)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, round_num: int, total_rounds: int, phase: str) -> str:
        phase_instr = PHASE_INSTRUCTIONS.get(phase, PHASE_INSTRUCTIONS["rebuttal"])
        return (
            f"You are '{self.name}' participating in a high-quality structured debate.\n"
            f"Your persona and perspective: {self.role}\n\n"
            f"━━ CURRENT PHASE: {PHASE_LABELS.get(phase, phase.upper())} "
            f"(Round {round_num} of {total_rounds}) ━━\n\n"
            f"{phase_instr}\n\n"
            f"UNIVERSAL RULES:\n"
            f"• Write 3–5 focused paragraphs. No filler, no padding.\n"
            f"• Stay strictly in character — every argument must reflect your persona's "
            f"worldview, values, and epistemic standards.\n"
            f"• Reference other debaters by name. Quote or paraphrase what they actually said.\n"
            f"• Never dodge a strong opposing argument. Engage with it or concede the point.\n"
            f"• End every response with a single sentence starting with 'POSITION: ' that "
            f"states your current stance (e.g. 'POSITION: I strongly support X because Y.')."
        )

    def _build_messages(
        self,
        topic: str,
        round_num: int,
        history: list[dict],
        moderator_prompt: Optional[str] = None,
    ) -> list[dict]:
        if not history:
            content = (
                f'The debate topic is: "{topic}"\n\n'
                f"You are the first to speak. Present your opening position."
            )
        else:
            transcript = format_history(history)
            content = (
                f'The debate topic is: "{topic}"\n\n'
                f"Debate transcript so far:\n{transcript}\n\n"
            )
            if moderator_prompt:
                content += (
                    f"━━ MODERATOR'S CHALLENGE FOR THIS ROUND ━━\n"
                    f"{moderator_prompt}\n\n"
                    f"Address the moderator's challenge in your response.\n\n"
                )
            content += f"It is now Round {round_num}. Give your response."
        return [{"role": "user", "content": content}]
