"""The replay page: everything escaped, nothing loaded from outside, the whole debate shown."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.replay import DISCLAIMER, load_transcript, render_replay, write_replay
from agora.transcript import build_transcript, save_transcript

EVIL = '<script>alert("x")</script><img src=x onerror=alert(1)>'


def _transcript(**kw):
    args = dict(
        topic=f"Ban cars? {EVIL}",
        agent_configs=[{"name": f"Ada {EVIL}"}, {"name": "Bo"}],
        planned_rounds=3,
        provider_label="fake/model",
        history=[
            {"round": 1, "phase": "opening", "agent": f"Ada {EVIL}", "text": f"Yes. {EVIL}\nPOSITION: I support it {EVIL}"},
            {"round": 1, "phase": "opening", "agent": "Bo", "text": "No.\nPOSITION: I oppose it."},
            {"round": 2, "phase": "closing", "agent": f"Ada {EVIL}", "text": "Still yes."},
            {"round": 2, "phase": "closing", "agent": "Bo", "text": "Fine.\nPOSITION: I support it now."},
        ],
        synthesis=f"Partly agreed. {EVIL}",
        consensus_scores=[0.254, 0.5],
        interventions={2: f"Bo, answer that. {EVIL}"},
        created=datetime(2026, 11, 19, 16, 30, 5, tzinfo=timezone.utc),
    )
    args.update(kw)
    return build_transcript(**args)


def test_model_text_is_escaped_everywhere():
    page = render_replay(_transcript())
    assert "<script" not in page.lower()
    assert "<img" not in page.lower()
    # topic (title, h1) 2 + agent name (meta line, table, 2 turns) 4 + speech (body and its POSITION: line) 2
    # + position (cell title, aria-label, turn) 3 + moderator 1 + synthesis 1: every copy escaped, none lost
    assert page.count("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;") == 13


def test_nothing_is_loaded_from_outside():
    page = render_replay(_transcript())
    assert not re.search(r"<(script|link|iframe|img|object|embed)\b", page, re.I)
    assert not re.search(r"https?://|@import|url\(", page, re.I)
    assert "default-src 'none'" in page


def test_page_shows_every_round_turn_score_and_the_synthesis():
    page = render_replay(_transcript())
    assert page.count('<article class="turn"') == 4
    assert 'id="round-1"' in page and 'id="round-2"' in page
    assert "Round 1 · Opening Statement" in page and "Round 2 · Closing Argument" in page
    assert ">25%<" in page and ">50%<" in page  # rounded like the Markdown report
    assert "Bo, answer that." in page
    assert "Partly agreed." in page
    assert page.count(DISCLAIMER) == 2
    assert "2 of 3 planned rounds" in page


def test_position_cells_follow_polarity_and_link_to_the_speech():
    page = render_replay(_transcript())
    cells = re.findall(r'<a class="cell (\w+)" href="#(r\d-t\d)" title="([^"]*)"', page)
    assert [(c, h) for c, h, _ in cells] == [
        ("for", "r1-t0"), ("none", "r2-t0"),       # Ada: support, then no POSITION: line
        ("against", "r1-t1"), ("for", "r2-t1"),    # Bo: oppose, then support
    ]
    assert cells[1][2] == "no POSITION: line"
    assert 'id="r2-t1"' in page


def test_a_round_without_score_says_so():
    page = render_replay(_transcript(consensus_scores=[0.25]))
    assert "no score" in page


def test_load_rejects_other_files_and_other_versions(tmp_path):
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"hello": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="not an agora transcript"):
        load_transcript(other)
    newer = tmp_path / "newer.json"
    newer.write_text(json.dumps({**_transcript(), "schema_version": 2}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema version 2"):
        load_transcript(newer)


def test_write_defaults_to_the_transcript_name(tmp_path):
    src = save_transcript(tmp_path / "debate_x.json", _transcript())
    out = write_replay(src)
    assert out.endswith("debate_x.html")
    assert (tmp_path / "debate_x.html").read_text(encoding="utf-8").startswith("<!doctype html>")


@pytest.fixture
def _offline(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def test_cli_turns_a_dry_run_into_a_replay(tmp_path, _offline):
    runner = CliRunner()
    result = runner.invoke(cli, [
        "run", "--dry-run", "--topic", "Should cities ban <cars>?", "--agents", "Ann,Bob",
        "--rounds", "3", "--no-stream", "--output", str(tmp_path),
    ])
    assert result.exit_code == 0, result.output
    (transcript,) = tmp_path.glob("debate_*.json")
    out = tmp_path / "page" / "replay.html"
    result = runner.invoke(cli, ["replay", str(transcript), "-o", str(out)])
    assert result.exit_code == 0, result.output
    page = out.read_text(encoding="utf-8")
    assert "<h1>Should cities ban &lt;cars&gt;?</h1>" in page
    assert page.count('<article class="turn"') == 6


def test_cli_reports_a_file_that_is_not_a_transcript(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    result = CliRunner().invoke(cli, ["replay", str(bad)])
    assert result.exit_code == 1
    text = " ".join(result.output.split())  # rich wraps long lines at the terminal width
    assert "not an agora transcript" in text
    assert text.count("bad.json") == 1
