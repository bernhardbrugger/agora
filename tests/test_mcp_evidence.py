"""--mcp-server / --mcp-call: tool results of a local MCP server become evidence cards."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.evidence import MAX_CARD_CHARS, EvidenceError
from agora.mcp_evidence import load_mcp_evidence, parse_call, split_command

FAKE = Path(__file__).resolve().parent / "fake_mcp_server.py"
SERVER = subprocess.list2cmdline([sys.executable, str(FAKE)]) if sys.platform == "win32" else f"'{sys.executable}' '{FAKE}'"
KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY")


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


# ── pure parsing: runs everywhere, no mcp package needed ──

def test_a_call_is_a_tool_name_with_optional_json_arguments():
    assert parse_call("notes") == ("notes", {})
    assert parse_call(' price {"symbol": "NVDA"} ') == ("price", {"symbol": "NVDA"})


@pytest.mark.parametrize("spec, message", [
    ("", "needs a tool name"),
    ("price {symbol: NVDA}", "not valid JSON"),
    ('price ["NVDA"]', "must be a JSON object"),
])
def test_bad_calls_are_refused_with_the_reason(spec, message):
    with pytest.raises(EvidenceError, match=message):
        parse_call(spec)


def test_the_server_command_keeps_quoted_paths_together():
    assert split_command('"C:/Program Files/py.exe" -m srv')[0] == "C:/Program Files/py.exe"
    with pytest.raises(EvidenceError, match="needs a command"):
        split_command("   ")


def test_calls_without_a_server_and_too_many_cards_are_refused():
    with pytest.raises(EvidenceError, match="needs --mcp-server"):
        load_mcp_evidence("", ["notes"])
    with pytest.raises(EvidenceError, match="at most 20"):
        load_mcp_evidence("srv", ["notes"] * 3, first_number=19)


def test_a_server_without_a_call_stops_the_run(tmp_path):
    result = CliRunner().invoke(cli, [
        "run", "--topic", "T", "--agents", "2", "--rounds", "2", "--dry-run",
        "--output", str(tmp_path), "--mcp-server", "anything",
    ])
    assert result.exit_code == 1
    assert "needs at least one --mcp-call" in result.output
    assert not list(tmp_path.iterdir())


# ── against a real stdio MCP server (tests/fake_mcp_server.py) ──

needs_mcp = pytest.mark.skipif(
    sys.version_info < (3, 10) or importlib.util.find_spec("mcp") is None,
    reason="the mcp package (Python 3.10+) is not installed",
)


@needs_mcp
def test_each_call_becomes_a_card_numbered_after_the_file_cards():
    cards = load_mcp_evidence(SERVER, ['price {"symbol": "NVDA"}', "notes"], first_number=2)
    assert [c["id"] for c in cards] == ["E2", "E3"]
    assert cards[0]["title"] == 'mcp: price {"symbol": "NVDA"}'
    assert cards[0]["text"] == "NVDA: close 101.5 on 2026-11-20 (fake data)"
    assert cards[1]["title"] == "mcp: notes"
    assert cards[1]["truncated"] is False


@needs_mcp
def test_a_long_result_is_cut_and_marked():
    (card,) = load_mcp_evidence(SERVER, ["long_text"])
    assert len(card["text"]) == MAX_CARD_CHARS
    assert card["truncated"] is True


@needs_mcp
def test_a_tool_error_and_an_unknown_tool_stop_with_the_tool_name():
    with pytest.raises(EvidenceError, match="^MCP tool broken returned an error: .*no data for this request"):
        load_mcp_evidence(SERVER, ["broken"])
    with pytest.raises(EvidenceError, match="nosuchtool"):
        load_mcp_evidence(SERVER, ["nosuchtool"])


@needs_mcp
def test_a_server_that_cannot_start_is_named():
    with pytest.raises(EvidenceError, match="failed"):
        load_mcp_evidence("agora-no-such-command-xyz", ["notes"])


@needs_mcp
def test_run_gives_the_tool_result_to_every_speaker_and_records_it(tmp_path):
    notes = tmp_path / "notes.md"
    notes.write_text("Budget rose 4%.", encoding="utf-8")
    out = tmp_path / "reports"
    result = CliRunner().invoke(cli, [
        "run", "--topic", "Is the stock cheap?", "--agents", "2", "--rounds", "2", "--dry-run",
        "--no-stream", "--output", str(out), "--evidence", str(notes),
        "--mcp-server", SERVER, "--mcp-call", 'price {"symbol": "NVDA"}', "--mcp-call", "notes",
    ])
    assert result.exit_code == 0, result.output
    (transcript,) = out.glob("*.json")
    evidence = json.loads(transcript.read_text(encoding="utf-8"))["evidence"]
    assert [(c["id"], c["title"]) for c in evidence] == [
        ("E1", "notes.md"), ("E2", 'mcp: price {"symbol": "NVDA"}'), ("E3", "mcp: notes"),
    ]
    report = transcript.with_suffix(".md").read_text(encoding="utf-8")
    assert "mcp: price" in report


def test_no_calls_means_no_cards_and_no_server_start():
    assert load_mcp_evidence("", []) == []
