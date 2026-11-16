"""--dry-run: a full debate offline, without an API key or a model call."""

from __future__ import annotations

import re

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.providers.base import LLMProvider
from agora.providers.dryrun import DryRunProvider

KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY")


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    # load_dotenv() in the CLI must not bring a developer's .env back
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def _run(tmp_path, *args):
    result = CliRunner().invoke(
        cli,
        ["run", "--dry-run", "--topic", "Should cities ban cars?", "--output", str(tmp_path), *args],
    )
    assert result.exit_code == 0, result.output
    reports = list(tmp_path.glob("debate_*.md"))
    assert len(reports) == 1
    return reports[0].read_text(encoding="utf-8")


def test_without_dry_run_a_missing_key_stops_the_run(tmp_path):
    result = CliRunner().invoke(cli, ["run", "--topic", "x", "--output", str(tmp_path)])
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output


def test_dry_run_writes_a_full_report_without_a_key(tmp_path):
    report = _run(tmp_path, "--agents", "3", "--rounds", "4", "--no-stream")
    assert "**Provider:** dryrun/canned" in report
    phases = re.findall(r"^## Round (\d) · ([^·]+?) · Consensus: \d+%$", report, re.M)
    assert phases == [
        ("1", "Opening Statement"),
        ("2", "Rebuttal"),
        ("3", "Cross-Examination"),
        ("4", "Closing Argument"),
    ]
    assert report.count("### The Devil's Advocate") == 4
    assert '[dry run] Canned synthesis for "Should cities ban cars?"' in report


def test_speakers_alternate_stances_then_all_support_in_closing(tmp_path):
    report = _run(tmp_path, "--agents", "Ann,Bob,Cy", "--rounds", "3", "--no-stream")
    positions = re.findall(r"^POSITION: I (\w+) it\.$", report, re.M)
    assert positions == ["support", "oppose", "support"] * 2 + ["support"] * 3
    trend = re.search(r"\*\*Consensus trend:\*\* (\d+)% → (\d+)% → (\d+)%", report)
    first, _, last = map(int, trend.groups())
    assert last > first


def test_streaming_and_plain_runs_give_the_same_transcript(tmp_path):
    streamed = _run(tmp_path / "s", "--agents", "2", "--rounds", "2")
    plain = _run(tmp_path / "p", "--agents", "2", "--rounds", "2", "--no-stream")

    def body(report):
        return report.split("---", 1)[1]

    assert body(streamed) == body(plain)


def test_provider_name_resolves_and_needs_no_key():
    provider = LLMProvider.resolve("dryrun")
    assert isinstance(provider, DryRunProvider)
    system = "You are 'Dr. O'Neil' participating in a high-quality structured debate."
    text = provider.complete(system, [{"role": "user", "content": 'The debate topic is: "T"'}])
    assert text.startswith("[dry run] Dr. O'Neil,")
    assert "".join(provider.stream(system, [{"role": "user", "content": ""}])) == provider.complete(
        system, [{"role": "user", "content": ""}]
    )
