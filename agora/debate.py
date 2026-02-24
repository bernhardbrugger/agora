"""Debate orchestration logic."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from agora.agent import Agent, PHASE_LABELS
from agora.moderator import Moderator
from agora.providers.base import LLMProvider
from agora import renderer


# ---------------------------------------------------------------------------
# Phase mapping
# ---------------------------------------------------------------------------

def determine_phase(round_num: int, total_rounds: int) -> str:
    """Map a round number to a debate phase name."""
    if round_num == 1:
        return "opening"
    if round_num == total_rounds:
        return "closing"
    # With 4+ rounds, second-to-last is cross-examination
    if total_rounds >= 4 and round_num == total_rounds - 1:
        return "cross_examination"
    return "rebuttal"


# ---------------------------------------------------------------------------
# Consensus calculation
# ---------------------------------------------------------------------------

def calculate_consensus(history: list[dict], round_num: int) -> float:
    """
    Calculate a consensus score (0.0–1.0) for the given round.

    Uses a weighted combination of:
    - Keyword-overlap Jaccard similarity across agent responses (60%)
    - Positional polarity alignment extracted from POSITION: tags (40%)
    """
    round_entries = [e for e in history if e["round"] == round_num]
    round_texts = [e["text"] for e in round_entries]

    if len(round_texts) < 2:
        return 1.0

    # ── Keyword overlap ─────────────────────────────────────────────
    _STOP = {
        "this", "that", "with", "from", "have", "been", "will", "would",
        "could", "should", "also", "about", "into", "than", "them", "then",
        "their", "there", "these", "those", "what", "when", "where", "which",
        "while", "more", "some", "such", "each", "make", "like", "just",
        "over", "very", "much", "many", "most", "other", "being", "does",
        "oder", "aber", "auch", "noch", "schon", "kann", "eine", "einen",
        "einem", "nicht", "sich", "sind", "wird", "dass", "dies", "diese",
        "position", "round", "argue", "argument", "think", "believe",
        "point", "agree", "disagree", "must", "need", "want", "said",
    }

    def keywords(text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-ZäöüÄÖÜß]{4,}\b", text.lower())
        return {w for w in words if w not in _STOP}

    kw_sets = [keywords(t) for t in round_texts]
    sims: list[float] = []
    for i in range(len(kw_sets)):
        for j in range(i + 1, len(kw_sets)):
            a, b = kw_sets[i], kw_sets[j]
            if not a and not b:
                sims.append(0.5)
            elif not a or not b:
                sims.append(0.0)
            else:
                sims.append(len(a & b) / len(a | b))
    keyword_score = sum(sims) / len(sims) if sims else 0.5

    # ── Position polarity ────────────────────────────────────────────
    _pos_pattern = re.compile(r"POSITION:\s*(.+?)(?:\n|$)", re.IGNORECASE)
    _FOR_WORDS = {"support", "favor", "favour", "agree", "endorse", "beneficial", "for", "yes", "should"}
    _AGAINST_WORDS = {"oppose", "against", "reject", "harmful", "disagree", "no", "should not", "bad"}

    def polarity(text: str) -> float:
        m = _pos_pattern.search(text)
        if not m:
            return 0.0
        pos = m.group(1).lower()
        score = sum(1.0 for w in _FOR_WORDS if w in pos)
        score -= sum(1.0 for w in _AGAINST_WORDS if w in pos)
        return max(-1.0, min(1.0, score))

    polarities = [polarity(t) for t in round_texts]
    if any(p != 0.0 for p in polarities):
        avg = sum(polarities) / len(polarities)
        variance = sum((p - avg) ** 2 for p in polarities) / len(polarities)
        position_score = max(0.0, 1.0 - variance)
        return 0.6 * keyword_score + 0.4 * position_score

    return keyword_score


# ---------------------------------------------------------------------------
# Main debate runner
# ---------------------------------------------------------------------------

def run_debate(
    topic: str,
    agent_configs: list[dict],
    rounds: int = 5,
    model: Optional[str] = None,
    provider_name: str = "anthropic",
    output_dir: str = "reports",
    stream: bool = True,
    dynamic: bool = False,
    convergence_threshold: float = 0.75,
    moderator_interventions: bool = True,
) -> str:
    """
    Run a full structured debate and return the path to the saved report.

    Debate structure:
      Round 1              → Opening statements
      Rounds 2 … N-2       → Rebuttals (with optional moderator interventions)
      Round N-1 (if N ≥ 4) → Cross-examination
      Round N              → Closing arguments

    With --dynamic, the debate can terminate early if the convergence threshold
    is met, jumping immediately to a closing round.
    """
    llm = LLMProvider.resolve(provider_name, model=model)
    provider_label = f"{provider_name}/{llm.display_name}"

    agents = [
        Agent(
            name=cfg["name"],
            role=cfg["role"],
            color=cfg.get("color", "white"),
            provider=llm,
        )
        for cfg in agent_configs
    ]
    agent_names = [a.name for a in agents]
    moderator = Moderator(provider=llm)

    renderer.print_header(topic, agent_names, rounds, provider_label)

    history: list[dict] = []
    consensus_scores: list[float] = []

    effective_rounds = rounds
    current_round = 0

    while current_round < effective_rounds:
        current_round += 1
        phase = determine_phase(current_round, effective_rounds)
        renderer.print_round_header(current_round, effective_rounds, phase)

        # ── Moderator intervention (skip round 1 — no history yet) ──────
        intervention: Optional[str] = None
        if moderator_interventions and current_round > 1 and consensus_scores:
            last_score = consensus_scores[-1]
            intervention = moderator.generate_intervention(
                topic, history, agent_names, current_round, last_score
            )
            if intervention:
                renderer.print_moderator_intervention(intervention, current_round)

        # ── Agent responses ──────────────────────────────────────────────
        for agent in agents:
            if stream:
                text = renderer.print_agent_response_stream(
                    agent, topic, current_round, effective_rounds,
                    history, phase, intervention,
                )
            else:
                renderer.print_thinking(agent.name)
                text = agent.respond(
                    topic, current_round, effective_rounds,
                    history, phase, intervention,
                )
                renderer.print_agent_response(agent.name, text, agent.color, phase)

            history.append({
                "round": current_round,
                "phase": phase,
                "agent": agent.name,
                "text": text,
            })

        # ── Consensus tracking ───────────────────────────────────────────
        score = calculate_consensus(history, current_round)
        consensus_scores.append(score)
        renderer.print_consensus_meter(score, current_round, consensus_scores)

        # ── Dynamic early termination ────────────────────────────────────
        if (
            dynamic
            and current_round >= 2
            and score >= convergence_threshold
            and current_round < effective_rounds
            and phase != "closing"
        ):
            renderer.print_convergence_notice(score)
            effective_rounds = current_round + 1  # one more closing round

    # ── Moderator final synthesis ────────────────────────────────────────
    renderer.print_thinking("Moderator")
    synthesis = moderator.synthesize(topic, history, agent_names, consensus_scores)
    renderer.print_moderator_synthesis(synthesis)

    report_path = _save_report(
        topic, agent_configs, effective_rounds, provider_label,
        history, synthesis, consensus_scores, output_dir,
    )
    renderer.print_saved(report_path)
    return report_path


# ---------------------------------------------------------------------------
# Report serialisation
# ---------------------------------------------------------------------------

def _save_report(
    topic: str,
    agent_configs: list[dict],
    rounds: int,
    provider_label: str,
    history: list[dict],
    synthesis: str,
    consensus_scores: list[float],
    output_dir: str,
) -> str:
    """Serialise the full debate as a Markdown report."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^\w]+", "_", topic.lower())[:40].strip("_")
    path = out / f"debate_{slug}_{timestamp}.md"

    trend = " → ".join(f"{s:.0%}" for s in consensus_scores)

    lines = [
        f"# Debate: {topic}",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Rounds:** {rounds}",
        f"**Provider:** {provider_label}",
        f"**Agents:** {', '.join(a['name'] for a in agent_configs)}",
        f"**Consensus trend:** {trend}",
        "",
        "---",
        "",
    ]

    current_round: Optional[int] = None
    for entry in history:
        if entry["round"] != current_round:
            current_round = entry["round"]
            phase = entry.get("phase", "")
            phase_label = PHASE_LABELS.get(phase, phase.upper()) if phase else ""
            score = consensus_scores[current_round - 1] if current_round <= len(consensus_scores) else None
            heading = f"## Round {current_round}"
            if phase_label:
                heading += f" · {phase_label}"
            if score is not None:
                heading += f" · Consensus: {score:.0%}"
            lines.append(heading)
            lines.append("")
        lines.append(f"### {entry['agent']}")
        lines.append("")
        lines.append(entry["text"])
        lines.append("")

    lines += [
        "---",
        "",
        "# Moderator Synthesis",
        "",
        synthesis,
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
