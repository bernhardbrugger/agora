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
* **Steelman** counts the turns from round 2 on in which a speaker stated the
  best argument of the other side in a ``STEELMAN:`` line, out of the turns
  where one was asked for. agora checks that the line is there, not how good
  it is.
* **Crux** counts the turns in which a speaker named, in a ``CRUX:`` line, the
  one question of fact or value that would change their position if it were
  answered the other way, out of all their turns. The Cruxes list quotes each
  speaker's latest one: what was still open for them when they last spoke.
  agora checks that the line is there; it does not match cruxes across speakers.

``POSITION:``, ``STEELMAN:`` and ``CRUX:`` lines never count as repeats or as
unsupported claims (a steelman restates the other side, a crux is a question).
"""

from __future__ import annotations

import re
from typing import Optional

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
# "STEELMAN: ..." at the start of a line, also with Markdown emphasis such as "**STEELMAN:** ..."
_STEELMAN = re.compile(r"^[ \t*_>]*STEELMAN[ \t*_]*:[ \t*_]*(.*?)[ \t*_]*$", re.I | re.M)
_CRUX = re.compile(r"^[ \t*_>]*CRUX[ \t*_]*:[ \t*_]*(.*?)[ \t*_]*$", re.I | re.M)


def stance(polarity: float) -> str:
    """Map a polarity (-1.0 to 1.0) to ``for``, ``against`` or ``neutral``."""
    if polarity > 0:
        return "for"
    if polarity < 0:
        return "against"
    return "neutral"


def _body(text: str) -> str:
    """The turn without its POSITION, STEELMAN and CRUX lines."""
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().upper().startswith("POSITION:") and not _STEELMAN.match(line) and not _CRUX.match(line)
    )


def _first_line(pattern: re.Pattern, text: str) -> Optional[str]:
    for match in pattern.finditer(text):
        said = " ".join(match.group(1).split())
        if said:
            return said
    return None


def steelman(text: str) -> Optional[str]:
    """The text of the first non-empty ``STEELMAN:`` line of a turn, or None."""
    return _first_line(_STEELMAN, text)


def crux(text: str) -> Optional[str]:
    """The text of the first non-empty ``CRUX:`` line of a turn, or None."""
    return _first_line(_CRUX, text)


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
    return {
        "name": name, "stances": [], "shifts": 0, "repeats": 0, "sources": [], "unsupported": 0,
        "steelman_due": 0, "steelmen": [], "crux_due": 0, "cruxes": [],
    }


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
            if rnd.get("number", 1) > 1:
                row["steelman_due"] += 1
                said_steelman = steelman(text)
                if said_steelman:
                    row["steelmen"].append({"round": rnd["number"], "text": said_steelman})
            row["crux_due"] += 1
            said_crux = crux(text)
            if said_crux:
                row["cruxes"].append({"round": rnd.get("number", 1), "text": said_crux})

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
        "steelman_due": sum(a["steelman_due"] for a in agents),
        "steelmen": sum(len(a["steelmen"]) for a in agents),
        "crux_due": sum(a["crux_due"] for a in agents),
        "cruxes": sum(len(a["cruxes"]) for a in agents),
    }


def steelman_cell(agent: dict) -> str:
    """``given/asked`` for one speaker, ``-`` when no steelman was asked for (a one-round debate)."""
    return f"{len(agent['steelmen'])}/{agent['steelman_due']}" if agent["steelman_due"] else "-"


def crux_cell(agent: dict) -> str:
    """``given/asked`` for one speaker, ``-`` when they never spoke."""
    return f"{len(agent['cruxes'])}/{agent['crux_due']}" if agent["crux_due"] else "-"


def latest_cruxes(scorecard: dict) -> list[tuple[str, dict]]:
    """Each speaker's latest crux as ``(name, {"round", "text"})``, in speaker order."""
    return [(a["name"], a["cruxes"][-1]) for a in scorecard["agents"] if a["cruxes"]]


def scorecard_markdown(scorecard: dict) -> str:
    """The scorecard as a Markdown section for the report."""
    lines = [
        "## Scorecard",
        "",
        "Computed from the transcript, no model involved. It scores the debate, not the truth of the topic.",
        "",
        "| Agent | Stance by round | Shifts | Moved | Repeats | Sources | Unsupported | Steelman | Crux |",
        "|-------|-----------------|--------|-------|---------|---------|-------------|----------|------|",
    ]
    for a in scorecard["agents"]:
        by_round = " → ".join(s or "-" for s in a["stances"]) or "-"
        moved = f"yes ({a['opening']} → {a['closing']})" if a["moved"] else "no"
        lines.append(f"| {a['name']} | {by_round} | {a['shifts']} | {moved} | {a['repeats']} | {len(a['sources'])} | {a['unsupported']} | {steelman_cell(a)} | {crux_cell(a)} |")
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
    lines += ["", "### Steelman", ""]
    if scorecard["steelman_due"]:
        lines.append(
            f"{scorecard['steelmen']} of {scorecard['steelman_due']} turn(s) from round 2 on stated the other side's "
            "best argument in a `STEELMAN:` line. agora checks that the line is there, not how good it is."
        )
        stated = [(a["name"], s) for a in scorecard["agents"] for s in a["steelmen"]]
        if stated:
            lines.append("")
            lines += [f"- **{name}** (round {s['round']}): {s['text']}" for name, s in stated]
    else:
        lines.append("A one-round debate asks for no steelman.")
    lines += ["", "### Cruxes", ""]
    lines.append(
        f"{scorecard['cruxes']} of {scorecard['crux_due']} turn(s) named, in a `CRUX:` line, the question that would "
        "change the speaker's position. Each speaker's latest one, what was still open when they last spoke:"
    )
    lines.append("")
    open_cruxes = latest_cruxes(scorecard)
    if open_cruxes:
        lines += [f"- **{name}** (round {c['round']}): {c['text']}" for name, c in open_cruxes]
    else:
        lines.append("No speaker named a crux.")
    return "\n".join(lines)
