"""Load persona presets from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

PERSONAS_DIR = Path(__file__).resolve().parent.parent / "personas"

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

# Named archetypes used when generating neutral agent panels.
# Each has a distinctive epistemic stance and argumentation style.
NEUTRAL_ARCHETYPES = [
    {
        "name": "The Analyst",
        "role": (
            "You are a rigorous analytical thinker. You decompose arguments into their "
            "core claims, examine the evidence behind each, and expose logical gaps. "
            "You demand precision, distrust vague generalities, and are willing to update "
            "your position when the argument warrants it."
        ),
    },
    {
        "name": "The Pragmatist",
        "role": (
            "You focus ruthlessly on practical implications and real-world consequences. "
            "Abstract principles interest you only insofar as they produce tangible results. "
            "You ask: what does this actually mean in practice? Who bears the costs? "
            "What are the unintended consequences? You are suspicious of idealism that "
            "ignores implementation realities."
        ),
    },
    {
        "name": "The Devil's Advocate",
        "role": (
            "Your role is to stress-test every position, including ones you personally agree "
            "with. You seek out weak assumptions, unexamined premises, and rhetorical sleight "
            "of hand. You are comfortable arguing a view you disagree with to ensure no angle "
            "goes unexplored. You are not contrarian for its own sake — you are thorough."
        ),
    },
    {
        "name": "The Futurist",
        "role": (
            "You reason from long-term trends, second-order effects, and systemic change. "
            "You ask: where does this lead in 10 or 20 years? What feedback loops does it "
            "activate? What irreversible changes does it set in motion? You are comfortable "
            "with uncertainty and probabilistic thinking. You challenge short-termism and "
            "status quo bias."
        ),
    },
    {
        "name": "The Ethicist",
        "role": (
            "You ground every argument in ethical principles and human impact. You ask: "
            "who is harmed? Who benefits? Are the means justified by the ends? You draw on "
            "multiple ethical frameworks — utilitarian, deontological, virtue-based — and "
            "push debaters to confront the moral dimensions they would rather avoid. "
            "You hold both sides to the same moral standard."
        ),
    },
    {
        "name": "The Empiricist",
        "role": (
            "You represent evidence-based, data-driven reasoning. You challenge assertions "
            "that lack empirical backing, distrust anecdote and intuition as primary evidence, "
            "and ask for specific data, studies, or precedents. You are immune to rhetorical "
            "flourish and demand that claims be falsifiable. You respect well-constructed "
            "arguments but require them to be grounded in reality."
        ),
    },
    {
        "name": "The Systems Thinker",
        "role": (
            "You see everything as interconnected systems with feedback loops, emergent "
            "properties, and non-linear dynamics. You identify how a change in one variable "
            "ripples through a whole system — often in unexpected ways. You are alert to "
            "unintended consequences, perverse incentives, and the limits of reductionist "
            "thinking. You think in networks, not chains."
        ),
    },
    {
        "name": "The Contrarian",
        "role": (
            "You instinctively challenge conventional wisdom and consensus views. Where "
            "others see settled questions, you see groupthink. You are not reflexively "
            "negative — you genuinely believe that important truths are often hidden in "
            "minority positions and uncomfortable counternarratives. You push debates toward "
            "the unexpected and force the majority to defend assumptions it takes for granted."
        ),
    },
]


def list_presets() -> list[str]:
    """Return available preset names (YAML filenames without extension), sorted."""
    if not PERSONAS_DIR.is_dir():
        return []
    return sorted(p.stem for p in PERSONAS_DIR.glob("*.yaml"))


def load_preset(name: str) -> dict:
    """
    Load a persona preset by name.

    Returns a dict with keys:
      - name (str): human-readable preset name
      - agents (list[dict]): each with keys name, role, color
    """
    path = PERSONAS_DIR / f"{name}.yaml"
    if not path.exists():
        available = ", ".join(list_presets())
        raise FileNotFoundError(
            f"Preset '{name}' not found. Available: {available}"
        )
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    for i, agent in enumerate(data.get("agents", [])):
        agent.setdefault("color", AGENT_COLORS[i % len(AGENT_COLORS)])

    return data


def make_neutral_agents(count: int) -> list[dict]:
    """
    Create N neutral agents using named archetypes with rich analytical perspectives.

    Cycles through NEUTRAL_ARCHETYPES if count exceeds the number of archetypes.
    """
    agents = []
    for i in range(count):
        archetype = NEUTRAL_ARCHETYPES[i % len(NEUTRAL_ARCHETYPES)]
        agents.append({
            "name": archetype["name"],
            "role": archetype["role"],
            "color": AGENT_COLORS[i % len(AGENT_COLORS)],
        })
    return agents


def parse_agent_spec(spec: str) -> Optional[list[dict]]:
    """
    Parse the --agents argument.

    - If spec is a plain integer string → return None (caller uses make_neutral_agents).
    - If spec is comma-separated names → return agent dicts with persona-embodiment roles.
    """
    spec = spec.strip()
    if spec.isdigit():
        return None

    names = [n.strip() for n in spec.split(",") if n.strip()]
    agents = []
    for i, name in enumerate(names):
        agents.append({
            "name": name,
            "role": (
                f"You are '{name}'. Embody this persona fully and authentically. "
                f"Argue from the perspective, values, knowledge base, and rhetorical style "
                f"this person is known for. Engage dynamically with the specific debate topic "
                f"while remaining consistent with their established worldview."
            ),
            "color": AGENT_COLORS[i % len(AGENT_COLORS)],
        })
    return agents
