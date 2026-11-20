"""Debate formats: institutional set-ups with fixed roles, phases and an output shape.

A format is a YAML file in this package (``agora/formats/<id>.yaml``)::

    name: "Investment Committee"         # shown in the terminal and the report
    description: "One line for `agora formats`."
    disclaimer: "Shown before the debate and at the top of the report."
    rules: "Appended to every role: what nobody in this format may do."
    roles:                               # 2-8 speakers, in speaking order
      - name: "The Bull"
        role: "Persona description, as in a preset."
    phases: [opening, rebuttal, cross_examination, closing]   # one per round
    synthesis: "What the moderator's final output must contain (the memo)."

``phases`` fixes the number of rounds; it must start with ``opening`` and end with
``closing``. Unlike presets, formats ship inside the package, so they also work from
a wheel.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from agora.agent import PHASE_INSTRUCTIONS
from agora.personas import AGENT_COLORS

FORMATS_DIR = Path(__file__).resolve().parent

_REQUIRED_TEXT = ("name", "description", "disclaimer", "synthesis")


class FormatError(ValueError):
    """A format file is missing a field or breaks a rule of the spec."""


def list_formats() -> list[str]:
    """Return the ids of the built-in formats, sorted."""
    return sorted(p.stem for p in FORMATS_DIR.glob("*.yaml"))


def validate_format(data: object, fmt_id: str = "format") -> dict:
    """Check a parsed format against the spec and return it normalised.

    Each role gets the format's ``rules`` appended and a terminal colour.
    """
    if not isinstance(data, dict):
        raise FormatError(f"{fmt_id}: a format must be a mapping")
    for key in _REQUIRED_TEXT:
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise FormatError(f"{fmt_id}: '{key}' must be a non-empty string")

    roles = data.get("roles")
    if not isinstance(roles, list) or not 2 <= len(roles) <= 8:
        raise FormatError(f"{fmt_id}: 'roles' must list 2 to 8 speakers")
    names: list[str] = []
    for role in roles:
        if not isinstance(role, dict) or not str(role.get("name", "")).strip() or not str(role.get("role", "")).strip():
            raise FormatError(f"{fmt_id}: every role needs a 'name' and a 'role'")
        names.append(role["name"].strip())
    if len(set(names)) != len(names):
        raise FormatError(f"{fmt_id}: role names must be unique")

    phases = data.get("phases")
    if not isinstance(phases, list) or len(phases) < 2:
        raise FormatError(f"{fmt_id}: 'phases' must list at least 2 rounds")
    unknown = [p for p in phases if p not in PHASE_INSTRUCTIONS]
    if unknown:
        raise FormatError(
            f"{fmt_id}: unknown phase {unknown[0]!r}; known: {', '.join(PHASE_INSTRUCTIONS)}"
        )
    if phases[0] != "opening" or phases[-1] != "closing":
        raise FormatError(f"{fmt_id}: 'phases' must start with opening and end with closing")

    rules = str(data.get("rules") or "").strip()
    agents = []
    for i, role in enumerate(roles):
        text = role["role"].strip()
        if rules:
            text += f"\n\nRules of this format: {rules}"
        agents.append({
            "name": role["name"].strip(),
            "role": text,
            "color": role.get("color", AGENT_COLORS[i % len(AGENT_COLORS)]),
        })

    return {
        "id": fmt_id,
        "name": data["name"].strip(),
        "description": data["description"].strip(),
        "disclaimer": data["disclaimer"].strip(),
        "agents": agents,
        "phases": list(phases),
        "synthesis": data["synthesis"].strip(),
    }


def load_format(fmt_id: str) -> dict:
    """Load and validate a built-in format by id (e.g. ``committee``)."""
    path = FORMATS_DIR / f"{fmt_id}.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"Format '{fmt_id}' not found. Available: {', '.join(list_formats())}"
        )
    with open(path, encoding="utf-8") as fh:
        return validate_format(yaml.safe_load(fh), fmt_id)
