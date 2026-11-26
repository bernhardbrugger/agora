"""Sample gallery (``agora gallery``): one replay page per format plus an index page.

Every sample runs offline with the ``dryrun`` provider, so building the gallery needs no key and
costs nothing. The speeches are canned placeholder text: the gallery shows what a replay page
looks like (positions, consensus meter, scorecard, evidence cards, memo headings), not what a
model would argue. The index says so at the top.

The output directory holds only static files: ``index.html`` and ``<slug>.html`` per sample, each
with the same Content-Security-Policy as a replay page (no network loads at all), every string
escaped. It can be served as is, e.g. from GitHub Pages.
"""

from __future__ import annotations

import tempfile
from html import escape
from pathlib import Path
from typing import Optional

from agora.replay import _CSS

# Each sample is a fixed topic for a format or a preset. Topics are general questions, fictional
# cases or plans: no named companies, no real persons, no ongoing real cases (see AGENTS.md).
SAMPLES: list[dict] = [
    {
        "slug": "committee",
        "format": "committee",
        "topic": "Should a small software company keep a year of operating costs in cash?",
    },
    {
        "slug": "court",
        "format": "court",
        "topic": "A fictional case: a bakery sues a neighbour whose tree blocks its delivery entrance",
    },
    {
        "slug": "redteam",
        "format": "redteam",
        "topic": "Plan: move a five-person team's production database to one self-hosted server",
        "evidence": [
            "The team has no on-call rota; incidents are handled during office hours.",
            "The current managed database costs 410 EUR a month; the server would cost 60 EUR.",
        ],
    },
    {
        "slug": "parliament",
        "format": "parliament",
        "topic": "A fictional bill: a four-day working week for all public-sector staff",
    },
    {
        "slug": "preset-tech-builders",
        "preset": "tech_builders",
        "rounds": 4,
        "topic": "Should cities ban private cars from their centres?",
    },
]

NOTE = (
    "These pages were generated with agora's --dry-run provider: the speeches are canned placeholder "
    "text, not a model's arguments. They show the layout of a replay page (positions per round, "
    "consensus meter, scorecard, evidence cards, the format's memo headings). Run a real provider to "
    "get a real debate."
)


def _sample_label(sample: dict) -> str:
    if sample.get("format"):
        from agora.formats import load_format

        return f"Format: {load_format(sample['format'])['name']}"
    from agora.personas import load_preset

    return f"Preset: {load_preset(sample['preset']).get('name', sample['preset'])}"


def render_index(entries: list[dict]) -> str:
    """The index page: one card per sample with a relative link to its replay page."""
    e = escape
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">",
        "<title>agora sample gallery</title>",
        f"<style>{_CSS}</style></head><body><main>",
        "<header><small>agora</small><h1>Sample gallery</h1>",
        f'<p class="note">{e(NOTE)}</p></header>',
    ]
    for entry in entries:
        out.append('<section class="turn">')
        out.append(f'<h3><a href="{e(entry["href"])}">{e(entry["topic"])}</a></h3>')
        out.append(f'<p class="meta">{e(entry["label"])} · {int(entry["rounds"])} rounds · {e(", ".join(entry["agents"]))}</p>')
        out.append("</section>")
    out.append("</main></body></html>")
    return "\n".join(out) + "\n"


def build_gallery(output_dir: str | Path, samples: Optional[list[dict]] = None) -> list[str]:
    """Run every sample offline, write its replay page and the index; return the written paths."""
    from rich.console import Console

    from agora import renderer
    from agora.debate import run_debate
    from agora.evidence import cards_from_texts
    from agora.mcp_server import resolve_request
    from agora.replay import load_transcript, write_replay

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    entries: list[dict] = []
    previous_console = renderer.console
    renderer.console = Console(quiet=True)  # four debates of terminal output would bury the result
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for sample in samples if samples is not None else SAMPLES:
                agent_configs, rounds, debate_format = resolve_request(
                    sample["topic"], sample.get("preset"), sample.get("format"), rounds=sample.get("rounds")
                )
                report = run_debate(
                    topic=sample["topic"],
                    agent_configs=agent_configs,
                    rounds=rounds,
                    provider_name="dryrun",
                    output_dir=tmp,
                    stream=False,
                    debate_format=debate_format,
                    evidence=cards_from_texts(sample.get("evidence", [])) or None,
                )
                transcript = Path(report).with_suffix(".json")
                page = write_replay(transcript, out / f"{sample['slug']}.html")
                written.append(page)
                t = load_transcript(transcript)
                entries.append({
                    "href": f"{sample['slug']}.html",
                    "topic": sample["topic"],
                    "label": _sample_label(sample),
                    "rounds": len(t["rounds"]),
                    "agents": [a["name"] for a in t["agents"]],
                })
    finally:
        renderer.console = previous_console
    index = out / "index.html"
    index.write_text(render_index(entries), encoding="utf-8")
    written.append(str(index))
    return written
