"""agora mcp: list_presets, list_formats and run_debate for MCP clients."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from agora.mcp_evidence import load_mcp_evidence
from agora.mcp_server import DebateRequestError, debate, formats_info, presets_info, resolve_request

KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY")


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)


# ── request checks and listings: run everywhere, no mcp package needed ──

def test_presets_and_formats_are_listed_with_their_speakers():
    presets = {p["id"]: p for p in presets_info()}
    assert "investment_styles" in presets
    assert len(presets["investment_styles"]["agents"]) >= 2
    formats = {f["id"]: f for f in formats_info()}
    assert set(formats) >= {"committee", "court", "redteam"}
    assert formats["committee"]["rounds"] >= 2
    assert formats["committee"]["disclaimer"]
    assert formats["court"]["roles"]


def test_a_format_fixes_rounds_and_speakers():
    agents, rounds, fmt = resolve_request("Buy a house?", format_id="committee")
    assert fmt["name"]
    assert rounds == len(fmt["phases"])
    assert agents == fmt["agents"]


def test_agents_as_number_or_names_and_rounds_default_to_five():
    agents, rounds, fmt = resolve_request("Topic", agents="2")
    assert (len(agents), rounds, fmt) == (2, 5, None)
    agents, _, _ = resolve_request("Topic", agents="CEO, CTO", rounds=3)
    assert [a["name"] for a in agents] == ["CEO", "CTO"]


@pytest.mark.parametrize("kwargs, message", [
    ({"topic": "  "}, "topic must not be empty"),
    ({"topic": "T", "preset": "investment_styles", "format_id": "committee"}, "either preset or format"),
    ({"topic": "T", "preset": "no_such_preset"}, "no_such_preset"),
    ({"topic": "T", "format_id": "no_such_format"}, "no_such_format"),
    ({"topic": "T", "format_id": "committee", "rounds": 99}, "leave out rounds"),
    ({"topic": "T", "rounds": 1}, "at least 2"),
    ({"topic": "T", "rounds": 13}, "at most 12"),
    ({"topic": "T", "agents": "9"}, "at most 8 speakers"),
    ({"topic": "T", "agents": "0"}, "at least one speaker"),
])
def test_requests_the_cli_would_refuse_or_ask_about_are_refused(kwargs, message):
    with pytest.raises(DebateRequestError, match=message):
        resolve_request(**kwargs)


def test_a_dry_run_returns_paths_then_the_report(tmp_path):
    text = debate("Should cities ban cars?", tmp_path, preset="investment_styles", rounds=2, dry_run=True)
    head, _, report = text.partition("\n\n")
    paths = dict(line.split(": ", 1) for line in head.splitlines())
    assert set(paths) == {"Report", "Transcript", "Replay"}
    for path in paths.values():
        assert Path(path).is_file() and Path(path).parent == tmp_path
    assert report == Path(paths["Report"]).read_text(encoding="utf-8")
    assert report.startswith("# Debate: Should cities ban cars?")
    assert json.loads(Path(paths["Transcript"]).read_text(encoding="utf-8"))["topic"] == "Should cities ban cars?"


def test_replay_can_be_left_out(tmp_path):
    text = debate("Topic", tmp_path, agents="2", rounds=2, dry_run=True, replay=False)
    assert "Replay:" not in text.partition("\n\n")[0]
    assert not list(tmp_path.glob("*.html"))


def test_a_missing_key_is_a_request_error_before_anything_is_written(tmp_path):
    with pytest.raises(DebateRequestError, match="ANTHROPIC_API_KEY"):
        debate("Topic", tmp_path, agents="2", rounds=2)
    assert not list(tmp_path.iterdir())


# ── through a real stdio connection: python -m agora mcp ──

needs_mcp = pytest.mark.skipif(
    sys.version_info < (3, 10) or importlib.util.find_spec("mcp") is None,
    reason="the mcp package (Python 3.10+) is not installed",
)


def _server(output: Path) -> str:
    argv = [sys.executable, "-m", "agora", "mcp", "--output", str(output)]
    return subprocess.list2cmdline(argv) if sys.platform == "win32" else " ".join(f"'{a}'" for a in argv)


@needs_mcp
def test_a_client_runs_a_debate_over_stdio(tmp_path):
    """The debate's terminal output must not leak into stdout, or the protocol breaks."""
    calls = ["list_formats", 'run_debate {"topic": "Ban cars?", "agents": "2", "rounds": 2, "dry_run": true}']
    formats, result = load_mcp_evidence(_server(tmp_path), calls)
    assert "committee" in formats["text"]
    assert result["text"].startswith(f"Report: {tmp_path}")
    assert "# Debate: Ban cars?" in result["text"]
    assert len(list(tmp_path.glob("*.html"))) == 1


@needs_mcp
def test_a_refused_request_reaches_the_client_as_a_tool_error(tmp_path):
    with pytest.raises(Exception, match="either preset or format"):
        load_mcp_evidence(_server(tmp_path), ['run_debate {"topic": "T", "preset": "investment_styles", "format": "committee"}'])


# ── evidence texts from the client ──

def test_evidence_texts_become_cards_in_report_and_transcript(tmp_path):
    text = debate(
        "Lower the voting age?", tmp_path, agents="2", rounds=2, dry_run=True,
        evidence=["Austria lowered the voting age to 16 in 2007.", "  Turnout of first-time voters  "],
    )
    head, _, report = text.partition("\n\n")
    transcript = json.loads(Path(dict(l.split(": ", 1) for l in head.splitlines())["Transcript"]).read_text("utf-8"))
    assert [(c["id"], c["text"]) for c in transcript["evidence"]] == [
        ("E1", "Austria lowered the voting age to 16 in 2007."),
        ("E2", "Turnout of first-time voters"),
    ]
    assert transcript["evidence"][0]["title"] == "from the MCP client, item 1"
    assert "- `E1` `from the MCP client, item 1` (45 characters)" in report
    assert "- `E2` `from the MCP client, item 2` (28 characters)" in report


def test_without_evidence_the_transcript_has_no_cards(tmp_path):
    head, _, _ = debate("Topic", tmp_path, agents="2", rounds=2, dry_run=True, evidence=[]).partition("\n\n")
    transcript = json.loads(Path(dict(l.split(": ", 1) for l in head.splitlines())["Transcript"]).read_text("utf-8"))
    assert not transcript.get("evidence")


@pytest.mark.parametrize("evidence, message", [
    (["fine", "   "], "evidence item 2 is empty"),
    (["x"] * 21, "at most 20 evidence cards"),
])
def test_bad_evidence_is_refused_before_anything_is_written(tmp_path, evidence, message):
    with pytest.raises(DebateRequestError, match=message):
        debate("Topic", tmp_path, agents="2", rounds=2, dry_run=True, evidence=evidence)
    assert not list(tmp_path.iterdir())


@needs_mcp
def test_a_client_passes_evidence_over_stdio(tmp_path):
    call = json.dumps({"topic": "T", "agents": "2", "rounds": 2, "dry_run": True, "evidence": ["Card text 42"]})
    (result,) = load_mcp_evidence(_server(tmp_path), [f"run_debate {call}"])
    transcript = json.loads(next(tmp_path.glob("*.json")).read_text("utf-8"))
    assert transcript["evidence"][0]["text"] == "Card text 42"
    assert "- `E1` `from the MCP client, item 1` (12 characters)" in result["text"]
