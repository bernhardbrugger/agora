"""The JSON transcript: built from the history, valid against docs/transcript.schema.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.transcript import build_transcript, save_transcript

SCHEMA = json.loads((Path(__file__).parent.parent / "docs" / "transcript.schema.json").read_text(encoding="utf-8"))

HISTORY = [
    {"round": 1, "phase": "opening", "agent": "Ada", "text": "Cars cost lives.\nPOSITION: I support the ban."},
    {"round": 1, "phase": "opening", "agent": "Bo", "text": "Shops need customers.\nPOSITION: I oppose it."},
    {"round": 2, "phase": "closing", "agent": "Ada", "text": "<b>Still</b> yes."},
    {"round": 2, "phase": "closing", "agent": "Bo", "text": "POSITION:   partly convinced  \nMore."},
]


def _transcript(**kw):
    args = dict(
        topic="Ban cars?",
        agent_configs=[{"name": "Ada", "role": "urbanist"}, {"name": "Bo"}],
        planned_rounds=3,
        provider_label="fake/model",
        history=HISTORY,
        synthesis="They partly agree.",
        consensus_scores=[0.25, 0.5],
        interventions={2: "Bo, answer Ada's safety point."},
        created=datetime(2026, 11, 19, 16, 30, 5, tzinfo=timezone.utc),
    )
    args.update(kw)
    return build_transcript(**args)


def test_transcript_matches_the_published_schema():
    jsonschema.validate(_transcript(), SCHEMA)


def test_rounds_group_turns_with_score_and_moderator():
    t = _transcript()
    assert [r["number"] for r in t["rounds"]] == [1, 2]
    assert [r["phase"] for r in t["rounds"]] == ["opening", "closing"]
    assert [r["consensus"] for r in t["rounds"]] == [0.25, 0.5]
    assert [r["moderator"] for r in t["rounds"]] == [None, "Bo, answer Ada's safety point."]
    assert [[turn["agent"] for turn in r["turns"]] for r in t["rounds"]] == [["Ada", "Bo"], ["Ada", "Bo"]]
    assert t["rounds"][1]["turns"][0]["text"] == "<b>Still</b> yes."  # stored raw; readers escape


def test_turns_carry_position_and_polarity():
    turns = [turn for r in _transcript()["rounds"] for turn in r["turns"]]
    assert [turn["position"] for turn in turns] == ["I support the ban.", "I oppose it.", None, "partly convinced"]
    assert [turn["polarity"] for turn in turns] == [1.0, -1.0, 0.0, 0.0]


def test_header_fields():
    t = _transcript()
    assert (t["schema"], t["schema_version"]) == ("agora.transcript", 1)
    assert t["created"] == "2026-11-19T16:30:05Z"
    assert t["planned_rounds"] == 3 and t["provider"] == "fake/model"
    assert t["agents"] == [{"name": "Ada", "role": "urbanist"}, {"name": "Bo", "role": ""}]


def test_a_round_without_score_is_null_and_still_valid():
    t = _transcript(consensus_scores=[0.25])
    assert t["rounds"][1]["consensus"] is None
    jsonschema.validate(t, SCHEMA)


def test_save_writes_utf8_json(tmp_path):
    path = save_transcript(tmp_path / "out" / "t.json", _transcript(topic="Städte ohne Autos?"))
    raw = Path(path).read_bytes()
    assert "Städte".encode("utf-8") in raw  # not ä
    assert json.loads(raw.decode("utf-8"))["topic"] == "Städte ohne Autos?"


@pytest.fixture
def _offline(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def test_run_writes_a_valid_transcript_next_to_the_report(tmp_path, _offline):
    result = CliRunner().invoke(cli, [
        "run", "--dry-run", "--topic", "Should cities ban cars?", "--agents", "Ann,Bob,Cy",
        "--rounds", "4", "--no-stream", "--output", str(tmp_path),
    ])
    assert result.exit_code == 0, result.output
    (report,) = tmp_path.glob("debate_*.md")
    transcript_path = report.with_suffix(".json")
    assert "Transcript saved" in result.output
    t = json.loads(transcript_path.read_text(encoding="utf-8"))
    jsonschema.validate(t, SCHEMA)
    assert t["provider"] == "dryrun/canned"
    assert [r["phase"] for r in t["rounds"]] == ["opening", "rebuttal", "cross_examination", "closing"]
    assert all(len(r["turns"]) == 3 for r in t["rounds"])
    # the same speeches as the Markdown report, and the moderator's words are kept
    md = report.read_text(encoding="utf-8")
    assert all(turn["text"] in md for r in t["rounds"] for turn in r["turns"])
    assert t["synthesis"] in md
    assert any(r["moderator"] for r in t["rounds"][1:])


def test_format_is_recorded_and_valid():
    from agora.formats import load_format

    fmt = load_format("committee")
    t = _transcript(debate_format=fmt)
    assert t["format"] == {"id": "committee", "name": "Investment Committee", "disclaimer": fmt["disclaimer"]}
    jsonschema.validate(t, SCHEMA)
    assert "format" not in _transcript()


def test_committee_run_writes_the_format_into_the_transcript(tmp_path, monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)
    result = CliRunner().invoke(
        cli, ["run", "--dry-run", "--format", "committee", "--topic", "t", "--no-stream", "--output", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    t = json.loads(next(tmp_path.glob("debate_*.json")).read_text(encoding="utf-8"))
    jsonschema.validate(t, SCHEMA)
    assert t["format"]["id"] == "committee"
