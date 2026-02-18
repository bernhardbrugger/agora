"""Load persona presets from YAML files."""

from __future__ import annotations

import os
from pathlib import Path

import yaml


PERSONAS_DIR = Path(__file__).resolve().parent.parent / "personas"

# Fallback colors assigned to agents in order
AGENT_COLORS = [
    "cyan",
    "magenta",
    "yellow",
    "green",
    "blue",
    "red",
    "bright_cyan",
    "bright_magenta",
]


def list_presets() -> list[str]:
    """Return available preset names (YAML filenames without extension)."""
    if not PERSONAS_DIR.is_dir():
        return []
    return sorted(p.stem for p in PERSONAS_DIR.glob("*.yaml"))


def load_preset(name: str) -> dict:
    """Load a persona preset by name.

    Returns dict with keys: name (str), agents (list of {name, role}).
    """
    path = PERSONAS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Preset '{name}' not found. Available: {', '.join(list_presets())}"
        )
    with open(path) as f:
        data = yaml.safe_load(f)

    # Assign colors to agents
    for i, agent in enumerate(data.get("agents", [])):
        agent.setdefault("color", AGENT_COLORS[i % len(AGENT_COLORS)])

    return data


def make_neutral_agents(count: int) -> list[dict]:
    """Create N neutral agents with generic analytical perspectives."""
    perspectives = [
        "You approach topics with careful analytical reasoning, weighing evidence on all sides.",
        "You focus on practical implications and real-world consequences of ideas.",
        "You play devil's advocate, probing for weaknesses in every argument.",
        "You seek creative and unconventional solutions that others might miss.",
        "You prioritize risk assessment and downside protection.",
        "You focus on human impact, ethics, and long-term societal effects.",
        "You think in systems and look for second-order effects and feedback loops.",
        "You ground discussions in data, precedent, and empirical evidence.",
    ]
    agents = []
    for i in range(count):
        agents.append({
            "name": f"Agent {i + 1}",
            "role": perspectives[i % len(perspectives)],
            "color": AGENT_COLORS[i % len(AGENT_COLORS)],
        })
    return agents


def parse_agent_spec(spec: str) -> list[dict] | None:
    """Parse the --agents argument.

    If spec is a number, returns None (caller should use make_neutral_agents).
    If spec is comma-separated names, returns agent dicts with generic roles.
    """
    spec = spec.strip()
    if spec.isdigit():
        return None  # signal to use neutral agents

    names = [n.strip() for n in spec.split(",") if n.strip()]
    agents = []
    for i, name in enumerate(names):
        agents.append({
            "name": name,
            "role": f"You are '{name}'. Embody this persona fully and argue from that perspective.",
            "color": AGENT_COLORS[i % len(AGENT_COLORS)],
        })
    return agents
