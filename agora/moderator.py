"""Active moderator that guides debate flow and synthesizes outcomes."""

from __future__ import annotations

from typing import Optional

from agora.providers.base import LLMProvider
from agora.agent import format_history


class Moderator:
    """
    An active debate moderator backed by an LLM provider.

    Responsibilities:
    1. Generate targeted mid-debate interventions when the discussion stalls.
    2. Produce a rigorous final synthesis with clear resolution and action items.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or LLMProvider.resolve("anthropic")

    # ------------------------------------------------------------------
    # Mid-debate intervention
    # ------------------------------------------------------------------

    def generate_intervention(
        self,
        topic: str,
        history: list[dict],
        agent_names: list[str],
        round_num: int,
        consensus_score: float,
    ) -> Optional[str]:
        """
        Analyse the debate so far and, if warranted, generate a Socratic challenge
        that forces debaters to engage with something they have ignored or glossed over.

        Returns a prompt string, or None if no intervention is needed.
        """
        transcript = format_history(history)

        system = (
            "You are a Socratic debate moderator with expertise in structured argumentation, "
            "logic, and epistemology. Your interventions are sharp and provocative — they expose "
            "evasions, surface hidden assumptions, and force intellectual confrontation. "
            "You are neutral on conclusions but demanding on argument quality."
        )

        user = (
            f'Debate topic: "{topic}"\n'
            f"Participants: {', '.join(agent_names)}\n"
            f"Consensus score after last round: {consensus_score:.0%} "
            f"(0% = total disagreement, 100% = full agreement)\n\n"
            f"Full transcript:\n{transcript}\n\n"
            f"━━ YOUR TASK ━━\n"
            f"You are about to introduce Round {round_num}. Decide whether an intervention "
            f"is needed, and if so, produce one.\n\n"
            f"Intervene if any of the following are true:\n"
            f"• Participants are arguing past each other without genuine engagement\n"
            f"• A critical dimension of the topic has been entirely ignored\n"
            f"• Arguments are being repeated without new development (circular debate)\n"
            f"• An unexamined assumption is driving the entire disagreement\n"
            f"• The debate would benefit from a concrete scenario, edge case, or thought experiment\n"
            f"• Consensus is artificially high (agents are agreeing superficially)\n\n"
            f"If you intervene: Write ONE precise, challenging question or scenario. "
            f"Address it to all participants. It must directly target the most important "
            f"gap or evasion in the debate so far. Be incisive, not generic.\n\n"
            f"If no intervention is needed: Output only the word NONE."
        )

        result = self.provider.complete(system, [{"role": "user", "content": user}], max_tokens=350)
        result = result.strip()
        return None if result.upper().startswith("NONE") else result

    # ------------------------------------------------------------------
    # Final synthesis
    # ------------------------------------------------------------------

    def synthesize(
        self,
        topic: str,
        history: list[dict],
        agent_names: list[str],
        consensus_scores: list[float],
    ) -> str:
        """
        Produce a comprehensive, opinionated synthesis of the full debate including
        resolution, unresolved cruxes, and actionable recommendations.
        """
        transcript = format_history(history)
        trend = " → ".join(f"{s:.0%}" for s in consensus_scores)

        system = (
            "You are a world-class debate analyst and decision scientist. "
            "Your syntheses are rigorous, specific, and opinionated where evidence warrants it. "
            "You do not produce vague 'on the one hand / on the other hand' summaries. "
            "You resolve debates where possible, and precisely diagnose why resolution is "
            "impossible where it is not. Your recommendations are concrete and actionable."
        )

        user = (
            f'Debate topic: "{topic}"\n'
            f"Participants: {', '.join(agent_names)}\n"
            f"Consensus trend across rounds: {trend}\n\n"
            f"Full debate transcript:\n{transcript}\n\n"
            f"━━ PRODUCE YOUR SYNTHESIS IN EXACTLY THIS FORMAT ━━\n\n"
            f"## The Real Crux\n"
            f"(2–3 sentences: What is the FUNDAMENTAL disagreement? Not surface-level — "
            f"what underlying value, empirical assumption, or definitional difference "
            f"drives the divergence? Name it precisely.)\n\n"
            f"## Strongest Arguments FOR\n"
            f"- (3–5 bullets: the most logically sound pro-arguments, noting who made them "
            f"and what evidence or reasoning supports them)\n\n"
            f"## Strongest Arguments AGAINST\n"
            f"- (3–5 bullets: same standard)\n\n"
            f"## Position Evolution\n"
            f"(For each participant: Did their position shift across rounds? What caused any "
            f"movement? Who was most intellectually honest? Who was most rigid?)\n\n"
            f"## Surprising Insights\n"
            f"- (2–4 bullets: genuinely novel, unexpected, or underexplored points "
            f"that emerged — things a casual observer might have missed)\n\n"
            f"## Common Ground\n"
            f"(What did participants actually agree on, even if implicitly? "
            f"What shared assumptions or values could serve as a foundation for resolution?)\n\n"
            f"## Unresolved Cruxes\n"
            f"- (Specific factual, empirical, or ethical questions that remain open — "
            f"and that, if answered, would most shift the outcome. "
            f"Frame each as a testable or resolvable question.)\n\n"
            f"## Final Recommendation\n"
            f"(A specific, actionable recommendation. If the topic is a yes/no question, "
            f"answer it. If it is a strategy question, name the strategy. "
            f"Hedge only where genuine uncertainty exists — epistemic cowardice is not balance. "
            f"State the key condition under which your recommendation would change.)\n\n"
            f"## Confidence Score\n"
            f"(A number 0–100 followed by one sentence of justification. "
            f"100 = certainty, 50 = genuine toss-up, 0 = the question cannot be answered.)"
        )

        return self.provider.complete(system, [{"role": "user", "content": user}], max_tokens=3000)
