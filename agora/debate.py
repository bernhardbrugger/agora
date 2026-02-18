"""Debate orchestration logic."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import anthropic

from agora.agent import Agent
from agora.moderator import Moderator
from agora import renderer


def calculate_consensus(history: list[dict], round_num: int) -> float:
    """Calculate consensus score for a given round using keyword overlap.

    Falls back to keyword overlap (no embeddings needed).
    Returns a float between 0 and 1.
    """
    round_texts = [e["text"] for e in history if e["round"] == round_num]
    if len(round_texts) < 2:
        return 1.0

    def extract_keywords(text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-ZäöüÄÖÜß]{4,}\b", text.lower())
        # Filter common stop words
        stop = {
            "this", "that", "with", "from", "have", "been", "will", "would",
            "could", "should", "also", "about", "into", "than", "them", "then",
            "their", "there", "these", "those", "what", "when", "where", "which",
            "while", "more", "some", "such", "each", "make", "like", "just",
            "over", "very", "much", "many", "most", "other", "being", "does",
            "oder", "aber", "auch", "noch", "schon", "kann", "eine", "einen",
            "einem", "nicht", "sich", "sind", "wird", "dass", "dies", "diese",
        }
        return {w for w in words if w not in stop}

    keyword_sets = [extract_keywords(t) for t in round_texts]
    if not any(keyword_sets):
        return 0.5

    # Pairwise Jaccard similarity
    similarities = []
    for i in range(len(keyword_sets)):
        for j in range(i + 1, len(keyword_sets)):
            a, b = keyword_sets[i], keyword_sets[j]
            if not a and not b:
                similarities.append(0.5)
            else:
                intersection = a & b
                union = a | b
                similarities.append(len(intersection) / len(union) if union else 0.5)

    return sum(similarities) / len(similarities) if similarities else 0.5


def run_debate(
    topic: str,
    agent_configs: list[dict],
    rounds: int = 3,
    output_dir: str = "reports",
) -> str:
    """Run a full debate and return the path to the saved report."""
    agents = [
        Agent(
            name=cfg["name"],
            role=cfg["role"],
            color=cfg.get("color", "white"),
        )
        for cfg in agent_configs
    ]
    agent_names = [a.name for a in agents]

    renderer.print_header(topic, agent_names, rounds)

    history: list[dict] = []

    for round_num in range(1, rounds + 1):
        renderer.print_round_header(round_num, rounds)

        for agent in agents:
            renderer.print_thinking(agent.name)
            text = agent.respond(topic, round_num, rounds, history)
            history.append({
                "round": round_num,
                "agent": agent.name,
                "text": text,
            })
            renderer.print_agent_response(agent.name, text, agent.color)

        # Consensus meter
        score = calculate_consensus(history, round_num)
        renderer.print_consensus_meter(score, round_num)

    # Moderator synthesis
    renderer.print_thinking("Moderator")
    moderator = Moderator()
    synthesis = moderator.synthesize(topic, history, agent_names)
    renderer.print_moderator_synthesis(synthesis)

    # Save report
    report_path = _save_report(topic, agent_configs, rounds, history, synthesis, output_dir)
    renderer.print_saved(report_path)

    return report_path


def _save_report(
    topic: str,
    agent_configs: list[dict],
    rounds: int,
    history: list[dict],
    synthesis: str,
    output_dir: str,
) -> str:
    """Save the debate as a Markdown report."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^\w]+", "_", topic.lower())[:40].strip("_")
    filename = f"debate_{slug}_{timestamp}.md"
    path = out / filename

    lines = [
        f"# Debate: {topic}",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Rounds:** {rounds}",
        f"**Agents:** {', '.join(a['name'] for a in agent_configs)}",
        f"",
        "---",
        "",
    ]

    for entry in history:
        lines.append(f"## [Round {entry['round']}] {entry['agent']}")
        lines.append("")
        lines.append(entry["text"])
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# Moderator Synthesis")
    lines.append("")
    lines.append(synthesis)
    lines.append("")

    path.write_text("\n".join(lines))
    return str(path)
