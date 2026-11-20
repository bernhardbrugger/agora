"""Replay page: one self-contained HTML file built from a JSON transcript.

The page loads nothing from outside (no scripts, fonts, images or styles from
another host) and escapes every string from the transcript, because speeches,
moderator notes and the synthesis are model output and therefore untrusted.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from agora.agent import PHASE_LABELS
from agora.transcript import SCHEMA_ID, SCHEMA_VERSION

DISCLAIMER = (
    "Every speech on this page was written by AI models playing roles. It explores arguments; "
    "it is not a statement of fact and not financial, legal, medical or any other advice. "
    "The consensus score measures how close the speeches are, not who is right."
)

_CSS = """
:root{--bg:#f7f5f0;--fg:#1d1b18;--muted:#6b665d;--card:#fff;--line:#e2ddd2;--for:#2f7d4f;--against:#b23a2e;--none:#b9b2a5;--accent:#2d4f8a}
@media (prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#ebe7df;--muted:#a19b90;--card:#1f2125;--line:#33363c;--for:#5cbf83;--against:#e0705f;--none:#5d6068;--accent:#8fb0ea}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 Georgia,"Times New Roman",serif}
main{max-width:820px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.9rem;line-height:1.2;margin:.2em 0 .3em}
h2{font-size:1.25rem;margin:2.2em 0 .6em;border-bottom:1px solid var(--line);padding-bottom:.3em}
.meta,.note,small{color:var(--muted);font-size:.88rem}
.note{border-left:3px solid var(--line);padding:.4em .8em;margin:1em 0}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:4px 6px;text-align:center;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
.cell{display:inline-block;width:1.4em;height:1.4em;border-radius:3px;background:var(--none);text-decoration:none}
.cell.for{background:var(--for)}.cell.against{background:var(--against)}
.bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden}
.bar span{display:block;height:100%;background:var(--accent)}
.turn{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:12px 0}
.turn h3{margin:0 0 .4em;font-size:1rem}
.text{white-space:pre-wrap;overflow-wrap:anywhere}
.position{font-style:italic}
.moderator{background:transparent;border-style:dashed}
"""


def _polarity_class(value: float) -> str:
    if value > 0:
        return "for"
    if value < 0:
        return "against"
    return "none"


def load_transcript(path: str | Path) -> dict:
    """Read a transcript file and check that this version of agora can show it."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA_ID:
        raise ValueError(f"{path} is not an agora transcript (missing \"schema\": \"{SCHEMA_ID}\")")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"{path} has transcript schema version {data.get('schema_version')!r}; "
            f"this agora reads version {SCHEMA_VERSION}"
        )
    return data


def render_replay(t: dict) -> str:
    """Return the replay page for a transcript as one HTML string."""
    e = escape  # quote=True by default: safe in text and in attribute values
    rounds = t["rounds"]
    agents = [a["name"] for a in t["agents"]]
    out: list[str] = []
    add = out.append

    add("<!doctype html>")
    add('<html lang="en"><head><meta charset="utf-8">')
    add('<meta name="viewport" content="width=device-width, initial-scale=1">')
    # no network at all: the page may only use what is inside this file
    add("<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">")
    add(f"<title>Debate: {e(t['topic'])}</title>")
    add(f"<style>{_CSS}</style></head><body><main>")

    add("<header>")
    add("<small>agora debate replay</small>")
    add(f"<h1>{e(t['topic'])}</h1>")
    add(
        f'<p class="meta">{e(t["created"])} · {e(t["provider"])} · '
        f"{len(rounds)} of {int(t['planned_rounds'])} planned rounds · {e(', '.join(agents))}</p>"
    )
    fmt = t.get("format")
    if fmt:
        add(f'<p class="meta">Format: {e(fmt["name"])}</p>')
        add(f'<p class="note"><strong>Disclaimer:</strong> {e(fmt["disclaimer"])}</p>')
    add(f'<p class="note">{e(DISCLAIMER)}</p>')
    add("</header>")

    # ── position timeline: one row per agent, one cell per round ─────────
    add("<h2>Positions</h2>")
    add("<table><thead><tr><th>Agent</th>")
    for r in rounds:
        add(f'<th><a href="#round-{int(r["number"])}">R{int(r["number"])}</a></th>')
    add("</tr></thead><tbody>")
    for i, name in enumerate(agents):
        add(f"<tr><td>{e(name)}</td>")
        for r in rounds:
            turn_idx = next((j for j, turn in enumerate(r["turns"]) if turn["agent"] == name), None)
            if turn_idx is None:
                add("<td></td>")
                continue
            turn = r["turns"][turn_idx]
            label = turn["position"] or "no POSITION: line"
            add(
                f'<td><a class="cell {_polarity_class(turn["polarity"])}" '
                f'href="#r{int(r["number"])}-t{turn_idx}" title="{e(label)}" aria-label="{e(label)}"></a></td>'
            )
        add("</tr>")
    add("</tbody></table>")
    add('<p class="meta">Green: for · red: against · grey: no position or undecided (from each speech\'s POSITION: line).</p>')

    # ── consensus per round ─────────────────────────────────────────────
    add("<h2>Consensus</h2>")
    add("<table><tbody>")
    for r in rounds:
        score = r["consensus"]
        if score is None:
            add(f'<tr><td>Round {int(r["number"])}</td><td colspan="2">no score</td></tr>')
            continue
        pct = f"{float(score):.0%}"
        add(
            f'<tr><td>Round {int(r["number"])}</td><td style="width:70%"><div class="bar">'
            f'<span style="width:{float(score) * 100:.1f}%"></span></div></td><td>{pct}</td></tr>'
        )
    add("</tbody></table>")

    # ── the debate itself ───────────────────────────────────────────────
    for r in rounds:
        n = int(r["number"])
        phase = PHASE_LABELS.get(r["phase"], r["phase"])
        add(f'<section id="round-{n}"><h2>Round {n} · {e(phase)}</h2>')
        if r["moderator"]:
            add(f'<div class="turn moderator"><h3>Moderator</h3><div class="text">{e(r["moderator"])}</div></div>')
        for j, turn in enumerate(r["turns"]):
            add(f'<article class="turn" id="r{n}-t{j}"><h3>{e(turn["agent"])}</h3>')
            if turn["position"]:
                add(f'<p class="position">Position: {e(turn["position"])}</p>')
            add(f'<div class="text">{e(turn["text"])}</div></article>')
        add("</section>")

    add('<section id="synthesis"><h2>Moderator synthesis</h2>')
    add(f'<div class="turn"><div class="text">{e(t["synthesis"])}</div></div></section>')
    if fmt:
        add(f'<p class="note"><strong>Disclaimer:</strong> {e(fmt["disclaimer"])}</p>')
    add(f'<p class="note">{e(DISCLAIMER)}</p>')
    add("</main></body></html>")
    return "\n".join(out) + "\n"


def write_replay(transcript_path: str | Path, output: str | Path | None = None) -> str:
    """Render a transcript file to HTML; by default next to it with the suffix .html."""
    t = load_transcript(transcript_path)
    target = Path(output) if output else Path(transcript_path).with_suffix(".html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_replay(t), encoding="utf-8")
    return str(target)
