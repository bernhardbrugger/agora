"""Debate scorecard: who changed position and who repeated themselves.

The scorecard is computed from the transcript without calling a model, so it is
cheap, deterministic and the same for every provider. It scores the *debate*,
never the truth of the topic: a speaker who moved may have been persuaded by a
good argument or by a bad one.

* **Stance per round** comes from the ``POSITION:`` line of each turn
  (``for`` / ``against`` / ``neutral``; ``-`` when the line is missing).
* **Shifts** counts how often a speaker's stance changed between rounds in which
  they stated one.
* **Repeats** counts sentences that restate one of the speaker's own earlier
  sentences almost word for word (same words, at least 80% overlap, 8+ words).
* **Sources** are the inline ``[source: ...]`` citations a speaker gave. agora
  lists them as cited; it does not open or check them.
* **Unsupported** counts sentences that state a figure (a percentage, an amount
  in millions or billions, a multiple) or lean on a study, survey, report or
  statistic, with no ``[source: ...]`` in the same sentence. This is a word
  pattern, not fact checking: a claim phrased without such words is missed.
"""

from __future__ import annotations

import re

REPEAT_MIN_WORDS = 8
REPEAT_OVERLAP = 0.8

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9']+")
_SOURCE = re.compile(r"\[source:\s*([^\]]+?)\s*\]", re.I)
_CLAIM = re.compile(
    r"\d[\d,.]*\s?(?:%|percent\b|per cent\b|million\b|billion\b|trillion\b|x\b|times\b)"
    r"|\b(?:stud(?:y|ies)|surveys?|statistics?|according to|research (?:shows?|finds?|found)"
    r"|data (?:shows?|suggests?)|reports? (?:that|shows?|found))\b",
    re.I,
)


def stance(polarity: float) -> str:
    """Map a polarity (-1.0 to 1.0) to ``for``, ``against`` or ``neutral``."""
    if polarity > 0:
        return "for"
    if polarity < 0:
        return "against"
    return "neutral"


def _body(text: str) -> str:
    """The turn without its POSITION line."""
    return "\n".join(line for line in text.splitlines() if not line.strip().upper().startswith("POSITION:"))


def sources(text: str) -> list[str]:
    """The ``[source: ...]`` citations in a turn, in order, without duplicates."""
    out: list[str] = []
    for match in _SOURCE.finditer(text):
        cited = " ".join(match.group(1).split())
        if cited not in out:
            out.append(cited)
    return out


def unsupported(text: str) -> int:
    """Sentences with a figure or a study/statistic cue but no ``[source: ...]``."""
    count = 0
    for sentence in _SENTENCE_SPLIT.split(_body(text)):
        if _CLAIM.search(_SOURCE.sub(" ", sentence)) and not _SOURCE.search(sentence):
            count += 1
    return count


def _sentences(text: str) -> list[frozenset[str]]:
    """Word sets of the sentences long enough to count, without the POSITION line."""
    out = []
    for sentence in _SENTENCE_SPLIT.split(_body(text)):
        words = _WORD.findall(sentence.lower())
        if len(words) >= REPEAT_MIN_WORDS:
            out.append(frozenset(words))
    return out


def _overlap(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b)


def _row(name: str) -> dict:
    return {"name": name, "stances": [], "shifts": 0, "repeats": 0, "sources": [], "unsupported": 0}


def build_scorecard(transcript: dict) -> dict:
    """Return the scorecard of a transcript (as written by ``build_transcript``)."""
    rows: dict[str, dict] = {a["name"]: _row(a["name"]) for a in transcript.get("agents", [])}
    said: dict[str, list[frozenset[str]]] = {name: [] for name in rows}

    for rnd in transcript.get("rounds", []):
        for turn in rnd.get("turns", []):
            name = turn["agent"]
            row = rows.setdefault(name, _row(name))
            earlier = said.setdefault(name, [])
            row["stances"].append(stance(turn.get("polarity", 0.0)) if turn.get("position") else None)
            sentences = _sentences(turn.get("text", ""))
            row["repeats"] += sum(1 for s in sentences if any(_overlap(s, e) >= REPEAT_OVERLAP for e in earlier))
            earlier.extend(sentences)
            text = turn.get("text", "")
            row["sources"] += [c for c in sources(text) if c not in row["sources"]]
            row["unsupported"] += unsupported(text)

    for row in rows.values():
        stated = [s for s in row["stances"] if s is not None]
        row["shifts"] = sum(1 for prev, cur in zip(stated, stated[1:]) if prev != cur)
        row["opening"] = stated[0] if stated else None
        row["closing"] = stated[-1] if stated else None
        row["moved"] = bool(stated) and stated[0] != stated[-1]

    agents = list(rows.values())
    return {
        "agents": agents,
        "moved": [a["name"] for a in agents if a["moved"]],
        "repeats": sum(a["repeats"] for a in agents),
        "unsupported": sum(a["unsupported"] for a in agents),
    }


def scorecard_markdown(scorecard: dict) -> str:
    """The scorecard as a Markdown section for the report."""
    lines = [
        "## Scorecard",
        "",
        "Computed from the transcript, no model involved. It scores the debate, not the truth of the topic.",
        "",
        "| Agent | Stance by round | Shifts | Moved | Repeats | Sources | Unsupported |",
        "|-------|-----------------|--------|-------|---------|---------|-------------|",
    ]
    for a in scorecard["agents"]:
        by_round = " → ".join(s or "-" for s in a["stances"]) or "-"
        moved = f"yes ({a['opening']} → {a['closing']})" if a["moved"] else "no"
        lines.append(f"| {a['name']} | {by_round} | {a['shifts']} | {moved} | {a['repeats']} | {len(a['sources'])} | {a['unsupported']} |")
    lines.append("")
    if scorecard["moved"]:
        lines.append(f"**Changed position:** {', '.join(scorecard['moved'])}.")
    else:
        lines.append("**Changed position:** nobody.")
    lines.append("")
    lines.append(
        f"**Repeated arguments:** {scorecard['repeats']} sentence(s) restated a speaker's own earlier sentence "
        f"(at least {REPEAT_OVERLAP:.0%} the same words)."
    )
    lines.append("")
    lines.append(
        f"**Unsupported claims:** {scorecard['unsupported']} sentence(s) gave a figure or leaned on a study, "
        "survey or statistic without a `[source: ...]` (a word pattern, not a fact check)."
    )
    cited = [(a["name"], c) for a in scorecard["agents"] for c in a["sources"]]
    lines += ["", "### Evidence", ""]
    if cited:
        lines.append("Sources as cited by the speakers. agora did not open or check them; a model can invent a source.")
        lines.append("")
        lines += [f"- **{name}:** {c}" for name, c in cited]
    else:
        lines.append("No speaker cited a source.")
    return "\n".join(lines)
