"""Machine-readable debate transcript (JSON, schema in docs/transcript.schema.json)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SCHEMA_ID = "agora.transcript"
SCHEMA_VERSION = 1

_POSITION_LINE = re.compile(r"POSITION:\s*(.+?)\s*(?:\n|$)", re.IGNORECASE)


def _position(text: str) -> Optional[str]:
    m = _POSITION_LINE.search(text)
    return m.group(1) if m else None


def build_transcript(
    topic: str,
    agent_configs: list[dict],
    planned_rounds: int,
    provider_label: str,
    history: list[dict],
    synthesis: str,
    consensus_scores: list[float],
    interventions: Optional[dict[int, str]] = None,
    created: Optional[datetime] = None,
) -> dict:
    """Return the whole debate as a JSON-ready dict (schema version 1)."""
    from agora.debate import position_polarity  # avoid an import cycle

    interventions = interventions or {}
    created = created or datetime.now(timezone.utc)

    rounds: list[dict] = []
    for entry in history:
        if not rounds or rounds[-1]["number"] != entry["round"]:
            number = entry["round"]
            rounds.append({
                "number": number,
                "phase": entry.get("phase", ""),
                "consensus": consensus_scores[number - 1] if number <= len(consensus_scores) else None,
                "moderator": interventions.get(number),
                "turns": [],
            })
        rounds[-1]["turns"].append({
            "agent": entry["agent"],
            "text": entry["text"],
            "position": _position(entry["text"]),
            "polarity": position_polarity(entry["text"]),
        })

    return {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "topic": topic,
        "created": created.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": provider_label,
        "planned_rounds": planned_rounds,
        "agents": [{"name": a["name"], "role": a.get("role", "")} for a in agent_configs],
        "rounds": rounds,
        "synthesis": synthesis,
    }


def save_transcript(path: str | Path, transcript: dict) -> str:
    """Write the transcript as UTF-8 JSON and return the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(p)
