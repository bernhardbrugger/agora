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
    # + position (cell title, aria-label, turn) 3 + moderator 1 + synthesis 1 + scorecard row 1:
    # every copy escaped, none lost
    assert page.count("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;") == 14


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


def test_format_name_and_disclaimer_are_shown_escaped():
    fmt = {"id": "x", "name": f"Court {EVIL}", "disclaimer": f"Not legal advice. {EVIL}"}
    html = render_replay(_transcript(debate_format=fmt))
    assert "<script" not in html and "<img" not in html
    assert "Format: Court &lt;script&gt;" in html
    assert html.count("<strong>Disclaimer:</strong> Not legal advice. &lt;script&gt;") == 2  # top and bottom


def test_no_format_disclaimer_without_a_format():
    assert "<strong>Disclaimer:</strong>" not in render_replay(_transcript())


def test_evidence_cards_are_shown_escaped_with_their_ids():
    cards = [
        {"id": "E1", "title": f"notes {EVIL}.md", "text": f"Trips fell 12%. {EVIL}", "truncated": False},
        {"id": "E2", "title": "long.txt", "text": "x" * 40, "truncated": True},
    ]
    html = render_replay(_transcript(evidence=cards))
    assert "<script" not in html.lower() and "<img" not in html.lower()
    assert "<h2>Evidence cards</h2>" in html
    assert '<details class="turn" id="card-E1"><summary><strong>E1</strong> notes &lt;script&gt;' in html
    assert "Trips fell 12%. &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in html
    assert "<strong>E2</strong> long.txt<small> · cut at 40 characters</small>" in html
    assert html.count("cut at") == 1  # E1 was not cut


def test_no_evidence_section_without_cards():
    assert "Evidence cards" not in render_replay(_transcript())


def test_run_with_replay_writes_the_page_next_to_the_report(tmp_path, _offline):
    result = CliRunner().invoke(
        cli,
        ["run", "--dry-run", "--format", "committee", "--topic", "Index funds?", "--no-stream",
         "--replay", "--output", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    report = next(tmp_path.glob("debate_*.md"))
    page = report.with_suffix(".html")
    assert page.is_file()
    html = page.read_text(encoding="utf-8")
    assert "<h1>Index funds?</h1>" in html and "Format: Investment Committee" in html
    assert "Replay saved" in " ".join(result.output.split())


def test_run_without_replay_writes_no_page(tmp_path, _offline):
    result = CliRunner().invoke(
        cli, ["run", "--dry-run", "--topic", "x", "--agents", "2", "--rounds", "2", "--no-stream", "--output", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert not list(tmp_path.glob("*.html"))


def test_scorecard_matches_the_report_numbers():
    page = render_replay(_transcript())
    section = page.split("<h2>Scorecard</h2>", 1)[1].split("<section", 1)[0]
    rows = re.findall(
        r"<tr><td>(.*?)</td><td>(.*?)</td><td>(\d+)</td><td>(.*?)</td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td><td>(.*?)</td></tr>",
        section,
    )
    assert [(name.startswith("Ada"), stances, shifts, moved) for name, stances, shifts, moved, *_ in rows] == [
        (True, "for → -", "0", "no"),                     # one stated stance: never "moved"
        (False, "against → for", "1", "yes (against → for)"),
    ]
    assert "Changed position: Bo." in section
    assert "Repeated arguments: 0 sentence(s)" in section
    assert "Unsupported claims: 0 sentence(s)" in section
    assert "No speaker cited a source." in section


def test_scorecard_shows_sources_and_unsupported_claims_like_the_report():
    t = _transcript(history=[
        {"round": 1, "phase": "opening", "agent": "Bo",
         "text": f"Traffic deaths fell 30% [source: Vision Zero report {EVIL}]. "
                 "A study found that most trips are short.\nPOSITION: I support it."},
        {"round": 2, "phase": "closing", "agent": "Bo",
         "text": "Costs rose 12 billion [source: https://example.org/costs].\nPOSITION: I support it."},
    ], agent_configs=[{"name": "Bo"}], consensus_scores=[0.5, 0.5], interventions={})
    section = render_replay(t).split("<h2>Scorecard</h2>", 1)[1].split("<section", 1)[0]
    row = re.search(r"<tr><td>Bo</td>(?:<td>.*?</td>){4}<td>(\d+)</td><td>(\d+)</td><td>.*?</td></tr>", section)
    assert row and row.groups() == ("2", "1")  # two sources cited, the study sentence has none
    assert "Unsupported claims: 1 sentence(s)" in section
    evidence = section.split("<h3>Evidence</h3>", 1)[1]
    assert evidence.count("<li>") == 2
    assert "<script" not in evidence and "Vision Zero report &lt;script&gt;" in evidence
    assert "<a " not in evidence and "https://example.org/costs" in evidence  # a cited URL is text, never a link


def test_scorecard_counts_repeats_and_names_nobody_when_nobody_moved():
    same = "Cars make every street louder and more dangerous for the children who walk there."
    t = _transcript(history=[
        {"round": 1, "phase": "opening", "agent": "Bo", "text": f"{same}\nPOSITION: I oppose it."},
        {"round": 2, "phase": "closing", "agent": "Bo", "text": f"{same}\nPOSITION: I oppose it."},
    ], agent_configs=[{"name": "Bo"}], consensus_scores=[0.5, 0.5], interventions={})
    section = render_replay(t).split("<h2>Scorecard</h2>", 1)[1]
    assert "Changed position: nobody." in section
    assert "Repeated arguments: 1 sentence(s)" in section


def test_scorecard_shows_the_steelman_column_and_list_escaped():
    t = _transcript(history=[
        {"round": 1, "phase": "opening", "agent": "Bo", "text": "No.\nPOSITION: I oppose it."},
        {"round": 2, "phase": "closing", "agent": "Bo",
         "text": f"Still no.\nSTEELMAN: Ada says quiet streets {EVIL} save lives.\nPOSITION: I oppose it."},
        {"round": 3, "phase": "closing", "agent": "Bo", "text": "No again.\nPOSITION: I oppose it."},
    ], agent_configs=[{"name": "Bo"}], consensus_scores=[0.5, 0.5, 0.5], interventions={})
    section = render_replay(t).split("<h2>Scorecard</h2>", 1)[1].split("<section", 1)[0]
    row = re.search(r"<tr><td>Bo</td>(?:<td>[^<]*</td>){6}<td>([^<]*)</td><td>[^<]*</td></tr>", section)
    assert row and row.group(1) == "1/2"
    steel = section.split("<h3>Steelman</h3>", 1)[1]
    assert "1 of 2 turn(s) from round 2 on" in steel
    assert steel.count("<li>") == 1 and "(round 2)" in steel
    assert "<script" not in steel and "quiet streets &lt;script&gt;" in steel


def test_one_round_replay_asks_for_no_steelman():
    t = _transcript(history=[
        {"round": 1, "phase": "opening", "agent": "Bo", "text": "No.\nPOSITION: I oppose it."},
    ], agent_configs=[{"name": "Bo"}], consensus_scores=[0.5], interventions={})
    section = render_replay(t).split("<h2>Scorecard</h2>", 1)[1].split("<section", 1)[0]
    assert re.search(r"<tr><td>Bo</td>(?:<td>[^<]*</td>){6}<td>-</td><td>0/1</td></tr>", section)
    assert "A one-round debate asks for no steelman." in section
    assert "No speaker named a crux." in section


def test_scorecard_shows_the_crux_column_and_the_latest_crux_escaped():
    t = _transcript(history=[
        {"round": 1, "phase": "opening", "agent": "Bo", "text": "No.\nCRUX: Do buses run on time?\nPOSITION: I oppose it."},
        {"round": 2, "phase": "closing", "agent": "Bo", "text": "Still no.\nPOSITION: I oppose it."},
        {"round": 3, "phase": "closing", "agent": "Bo",
         "text": f"No again.\nCRUX: Would {EVIL} shops survive?\nPOSITION: I oppose it."},
    ], agent_configs=[{"name": "Bo"}], consensus_scores=[0.5, 0.5, 0.5], interventions={})
    section = render_replay(t).split("<h2>Scorecard</h2>", 1)[1].split("<section", 1)[0]
    assert "<th>Steelman</th><th>Crux</th></tr>" in section
    assert re.search(r"<tr><td>Bo</td>(?:<td>[^<]*</td>){7}<td>2/3</td></tr>", section)
    cruxes = section.split("<h3>Cruxes</h3>", 1)[1]
    assert "2 of 3 turn(s) named" in cruxes
    assert cruxes.count("<li>") == 1 and "(round 3)" in cruxes and "buses" not in cruxes
    assert "<script" not in cruxes and "Would &lt;script&gt;" in cruxes
