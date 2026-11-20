"""Debate formats: the YAML spec, the committee format and `agora run --format`."""

from __future__ import annotations

import json
import re

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.formats import FormatError, list_formats, load_format, validate_format

KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY")


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def _spec(**over):
    spec = {
        "name": "Test",
        "description": "d",
        "disclaimer": "Not advice.",
        "synthesis": "## Memo\n(text)",
        "roles": [{"name": "A", "role": "ra"}, {"name": "B", "role": "rb"}],
        "phases": ["opening", "rebuttal", "closing"],
    }
    spec.update(over)
    return spec


def test_every_builtin_format_loads():
    assert "committee" in list_formats()
    for fmt_id in list_formats():
        fmt = load_format(fmt_id)
        assert fmt["id"] == fmt_id
        assert fmt["phases"][0] == "opening" and fmt["phases"][-1] == "closing"


def test_committee_has_its_roles_disclaimer_and_memo():
    fmt = load_format("committee")
    assert [a["name"] for a in fmt["agents"]] == [
        "The Bull", "The Bear", "The Risk Officer", "The Quant", "The Devil's Advocate",
    ]
    assert fmt["phases"] == ["opening", "rebuttal", "cross_examination", "closing"]
    assert "Not investment advice" in fmt["disclaimer"]
    assert "## Dissent" in fmt["synthesis"]
    # the format's rules reach every speaker's role
    for agent in fmt["agents"]:
        assert "Never recommend buying, selling, holding" in agent["role"]


def test_rules_are_appended_and_colours_assigned():
    fmt = validate_format(_spec(rules="No names."), "t")
    assert fmt["agents"][0]["role"] == "ra\n\nRules of this format: No names."
    assert fmt["agents"][0]["color"] != fmt["agents"][1]["color"]
    assert validate_format(_spec(), "t")["agents"][0]["role"] == "ra"


@pytest.mark.parametrize(
    "over, message",
    [
        ({"disclaimer": "  "}, "'disclaimer' must be a non-empty string"),
        ({"synthesis": None}, "'synthesis' must be a non-empty string"),
        ({"roles": [{"name": "A", "role": "r"}]}, "2 to 8 speakers"),
        ({"roles": [{"name": "A", "role": "r"}, {"name": "B"}]}, "needs a 'name' and a 'role'"),
        ({"roles": [{"name": "A", "role": "r"}, {"name": "A", "role": "s"}]}, "unique"),
        ({"phases": ["opening", "verdict", "closing"]}, "unknown phase 'verdict'"),
        ({"phases": ["rebuttal", "closing"]}, "start with opening and end with closing"),
        ({"phases": ["opening", "rebuttal"]}, "start with opening and end with closing"),
        ({"phases": ["closing"]}, "at least 2 rounds"),
    ],
)
def test_invalid_specs_are_rejected(over, message):
    with pytest.raises(FormatError, match=re.escape(message)):
        validate_format(_spec(**over), "t")


def test_unknown_format_names_the_available_ones():
    with pytest.raises(FileNotFoundError, match="Available: .*committee"):
        load_format("nope")


def _run(tmp_path, *args):
    return CliRunner().invoke(
        cli,
        ["run", "--dry-run", "--topic", "Is the thesis sound?", "--output", str(tmp_path), "--no-stream", *args],
    )


def test_committee_dry_run_follows_the_format(tmp_path):
    result = _run(tmp_path, "--format", "committee")
    assert result.exit_code == 0, result.output
    assert "Disclaimer:" in result.output

    report = next(tmp_path.glob("debate_*.md")).read_text(encoding="utf-8")
    assert "**Format:** Investment Committee" in report
    assert "> **Disclaimer:** Educational simulation of an investment committee" in report
    assert "**Agents:** The Bull, The Bear, The Risk Officer, The Quant, The Devil's Advocate" in report
    phases = re.findall(r"^## Round (\d) · ([^·]+?) · Consensus", report, re.M)
    assert phases == [
        ("1", "Opening Statement"), ("2", "Rebuttal"), ("3", "Cross-Examination"), ("4", "Closing Argument"),
    ]
    # the moderator wrote the committee memo, not the default synthesis
    assert "## Dissent" in report and "## What Would Change Our Minds" in report
    assert "## Final Recommendation" not in report

    transcript = json.loads(next(tmp_path.glob("debate_*.json")).read_text(encoding="utf-8"))
    assert transcript["planned_rounds"] == 4


def test_format_and_preset_cannot_be_combined(tmp_path):
    result = _run(tmp_path, "--format", "committee", "--preset", "neutral")
    assert result.exit_code == 1
    assert "either --format or --preset" in result.output


def test_format_fixes_the_number_of_rounds(tmp_path):
    result = _run(tmp_path, "--format", "committee", "--rounds", "6")
    assert result.exit_code == 1
    assert "has 4 rounds" in result.output
    assert _run(tmp_path, "--format", "committee", "--rounds", "4").exit_code == 0


def test_unknown_format_is_an_error(tmp_path):
    result = _run(tmp_path, "--format", "nope")
    assert result.exit_code == 1
    assert "Format 'nope' not found" in result.output


def test_formats_command_lists_committee():
    result = CliRunner().invoke(cli, ["formats"])
    assert result.exit_code == 0, result.output
    assert "committee" in result.output and "Investment Committee (4 rounds)" in result.output


def test_runs_without_a_format_keep_five_rounds_and_no_disclaimer(tmp_path):
    result = _run(tmp_path, "--agents", "2")
    assert result.exit_code == 0, result.output
    report = next(tmp_path.glob("debate_*.md")).read_text(encoding="utf-8")
    assert "**Rounds:** 5" in report
    assert "**Format:**" not in report and "Disclaimer" not in report
    assert "## Final Recommendation" in report


def test_a_format_sets_the_phase_of_every_round(tmp_path):
    from agora.debate import run_debate

    fmt = validate_format(_spec(phases=["opening", "cross_examination", "closing"]), "t")
    path = run_debate(
        topic="x", agent_configs=fmt["agents"], rounds=3, provider_name="dryrun",
        output_dir=str(tmp_path), stream=False, moderator_interventions=False, debate_format=fmt,
    )
    report = open(path, encoding="utf-8").read()
    # without the format, 3 rounds would be opening, rebuttal, closing
    assert re.findall(r"^## Round \d · ([^·]+?) · ", report, re.M) == [
        "Opening Statement", "Cross-Examination", "Closing Argument",
    ]
    assert "## Memo\nPlaceholder." in report
