"""Tests for the sample gallery (agora gallery): offline replays plus an index page."""

from __future__ import annotations

import re
from html import escape

import pytest
from click.testing import CliRunner

from agora import renderer
from agora.cli import cli
from agora.gallery import NOTE, SAMPLES, build_gallery, render_index
from agora.mcp_server import resolve_request


@pytest.fixture
def _offline(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def test_every_sample_is_a_valid_request_with_a_unique_slug():
    slugs = [s["slug"] for s in SAMPLES]
    assert len(slugs) == len(set(slugs))
    for sample in SAMPLES:
        assert bool(sample.get("format")) != bool(sample.get("preset")), sample["slug"]
        resolve_request(sample["topic"], sample.get("preset"), sample.get("format"), rounds=sample.get("rounds"))


def test_every_format_has_a_sample():
    from agora.formats import list_formats

    assert set(list_formats()) <= {s.get("format") for s in SAMPLES}


def test_build_writes_one_page_per_sample_and_an_index(tmp_path):
    samples = [
        {"slug": "one", "format": "redteam", "topic": "Plan <A>", "evidence": ["Card text & more"]},
        {"slug": "two", "preset": "tech_builders", "rounds": 3, "topic": "Topic B"},
    ]
    paths = build_gallery(tmp_path / "out", samples)

    out = tmp_path / "out"
    assert sorted(p.name for p in out.iterdir()) == ["index.html", "one.html", "two.html"]
    assert [p.replace("\\", "/").rsplit("/", 1)[-1] for p in paths] == ["one.html", "two.html", "index.html"]
    one = (out / "one.html").read_text(encoding="utf-8")
    assert "Plan &lt;A&gt;" in one and "Card text &amp; more" in one  # the replay page, with its evidence card
    index = (out / "index.html").read_text(encoding="utf-8")
    assert re.findall(r'href="([^"]+)"', index) == ["one.html", "two.html"]
    assert "Format: Red Team Review · 4 rounds" in index
    assert "Preset: Tech Builders · 3 rounds" in index


def test_build_leaves_the_terminal_quiet_and_restores_the_console(tmp_path, capsys):
    before = renderer.console
    build_gallery(tmp_path, [{"slug": "s", "preset": "tech_builders", "rounds": 2, "topic": "T"}])
    assert renderer.console is before
    assert capsys.readouterr().out == ""


def test_index_escapes_text_says_it_is_canned_and_loads_nothing():
    page = render_index([{
        "href": "x.html", "topic": "<script>alert(1)</script>", "label": "Format: <b>",
        "rounds": 4, "agents": ["A&B"],
    }])
    assert "<script>" not in page
    assert "&lt;script&gt;" in page and "Format: &lt;b&gt;" in page and "A&amp;B" in page
    assert "default-src 'none'" in page
    assert escape(NOTE) in page
    assert not re.search(r'(?:src|href)="(?:https?:)?//', page)


def test_cli_builds_the_full_gallery(tmp_path, _offline):
    result = CliRunner().invoke(cli, ["gallery", "--output", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [f"{s['slug']}.html" for s in SAMPLES] + ["index.html"]
    )
    assert "placeholder" in result.output
