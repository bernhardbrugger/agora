"""Tests for the pure logic: phases, consensus, presets, agent specs, transcripts, reports.

No test calls a real LLM provider.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agora import personas
from agora.agent import PHASE_INSTRUCTIONS, PHASE_LABELS, format_history
from agora.debate import _save_report, calculate_consensus, determine_phase, position_polarity


# ── determine_phase ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "total, expected",
    [
        (1, ["opening"]),
        (2, ["opening", "closing"]),
        (3, ["opening", "rebuttal", "closing"]),
        (4, ["opening", "rebuttal", "cross_examination", "closing"]),
        (6, ["opening", "rebuttal", "rebuttal", "rebuttal", "cross_examination", "closing"]),
    ],
)
def test_phase_sequence(total, expected):
    assert [determine_phase(r, total) for r in range(1, total + 1)] == expected


def test_every_phase_has_instructions_and_a_label():
    phases = {determine_phase(r, t) for t in range(1, 8) for r in range(1, t + 1)}
    assert phases == set(PHASE_INSTRUCTIONS) == set(PHASE_LABELS)


# ── calculate_consensus ─────────────────────────────────────────────────────

def _round(*texts, round_num=1):
    return [{"round": round_num, "agent": f"A{i}", "text": t} for i, t in enumerate(texts)]


def test_single_speaker_is_full_consensus():
    assert calculate_consensus(_round("Nuclear energy reduces emissions."), 1) == 1.0


def test_only_the_requested_round_counts():
    history = _round("alpha beta gamma delta", "alpha beta gamma delta") + _round(
        "nuclear energy reduces emissions", "tariffs protect domestic industry", round_num=2
    )
    assert calculate_consensus(history, 1) == 1.0
    assert calculate_consensus(history, 2) == 0.0


def test_keyword_overlap_is_jaccard_without_stop_words():
    # keywords: {nuclear, energy, cheap} and {nuclear, energy, expensive} -> 2 / 4
    history = _round("Nuclear energy is cheap.", "Nuclear energy would be expensive.")
    assert calculate_consensus(history, 1) == pytest.approx(0.5)


def test_keyword_overlap_averages_all_pairs():
    history = _round("solar panels", "solar panels", "wind turbines")
    # pairs: 1.0, 0.0, 0.0
    assert calculate_consensus(history, 1) == pytest.approx(1 / 3)


def test_agreeing_positions_raise_the_score():
    agree = _round(
        "Solar panels work.\nPOSITION: I support this.",
        "Wind turbines work.\nPOSITION: I support this too.",
    )
    split = _round(
        "Solar panels work.\nPOSITION: I support this.",
        "Wind turbines work.\nPOSITION: I oppose this.",
    )
    # keywords {solar, panels, work, support} vs {wind, turbines, work, support} = 2/6,
    # and vs {wind, turbines, work, oppose} = 1/7
    assert calculate_consensus(agree, 1) == pytest.approx(0.6 * 2 / 6 + 0.4 * 1.0)
    assert calculate_consensus(split, 1) == pytest.approx(0.6 * 1 / 7 + 0.4 * 0.0)


def test_score_stays_between_zero_and_one():
    history = _round(
        "POSITION: support favor agree endorse yes",
        "POSITION: oppose against reject harmful bad",
        "",
    )
    assert 0.0 <= calculate_consensus(history, 1) <= 1.0


# ── presets ─────────────────────────────────────────────────────────────────

def test_every_preset_loads_with_named_agents_and_colors():
    names = personas.list_presets()
    assert len(names) >= 16
    for name in names:
        data = personas.load_preset(name)
        assert data.get("name"), name
        agents = data["agents"]
        assert len(agents) >= 2, name
        for agent in agents:
            assert agent["name"].strip() and agent["role"].strip(), name
            assert agent["color"] in personas.AGENT_COLORS, name


def test_unknown_preset_names_the_available_ones():
    with pytest.raises(FileNotFoundError, match="neutral"):
        personas.load_preset("no_such_preset")


def test_list_presets_is_empty_without_the_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(personas, "PERSONAS_DIR", tmp_path / "missing")
    assert personas.list_presets() == []


# ── agent specs ─────────────────────────────────────────────────────────────

def test_neutral_agents_cycle_archetypes_and_colors():
    n = len(personas.NEUTRAL_ARCHETYPES) + 2
    agents = personas.make_neutral_agents(n)
    assert len(agents) == n
    assert agents[0]["name"] == agents[len(personas.NEUTRAL_ARCHETYPES)]["name"] == "The Analyst"
    assert [a["color"] for a in agents[:3]] == personas.AGENT_COLORS[:3]


def test_numeric_agent_spec_means_neutral_panel():
    assert personas.parse_agent_spec(" 4 ") is None


def test_named_agent_spec_builds_one_agent_per_name():
    agents = personas.parse_agent_spec("Skeptic, Optimist ,, Economist")
    assert [a["name"] for a in agents] == ["Skeptic", "Optimist", "Economist"]
    assert all(f"'{a['name']}'" in a["role"] for a in agents)


# ── transcript and report ───────────────────────────────────────────────────

HISTORY = [
    {"round": 1, "phase": "opening", "agent": "Ada", "text": "First."},
    {"round": 1, "phase": "opening", "agent": "Bo", "text": "Second."},
    {"round": 2, "phase": "closing", "agent": "Ada", "text": "Last."},
]


def test_format_history_groups_by_round_with_phase_labels():
    text = format_history(HISTORY)
    assert text.count("── Round 1 · Opening Statement ──") == 1
    assert text.count("── Round 2 · Closing Argument ──") == 1
    assert text.index("[Bo]:\nSecond.") < text.index("Round 2")
    assert format_history([]) == ""


def test_report_contains_rounds_scores_and_synthesis(tmp_path):
    path = _save_report(
        topic="Is remote work better? (2026)",
        agent_configs=[{"name": "Ada"}, {"name": "Bo"}],
        rounds=2,
        provider_label="fake",
        history=HISTORY,
        synthesis="They partly agree.",
        consensus_scores=[0.25, 0.5],
        output_dir=str(tmp_path / "reports"),
    )
    assert re.search(r"debate_is_remote_work_better_2026_\d{8}_\d{6}\.md$", path)
    report = open(path, encoding="utf-8").read()
    assert "**Agents:** Ada, Bo" in report
    assert "**Consensus trend:** 25% → 50%" in report
    assert "## Round 1 · Opening Statement · Consensus: 25%" in report
    assert "## Round 2 · Closing Argument · Consensus: 50%" in report
    assert report.rstrip().endswith("They partly agree.")


# ── position polarity ───────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "text, expected",
    [
        ("POSITION: I support the economic plan.", 1.0),       # "economic" contains "no"
        ("POSITION: I oppose it, as I said before.", -1.0),    # "before" contains "for"
        ("POSITION: I disagree.", -1.0),                       # "disagree" contains "agree"
        ("POSITION: We should not do this.", -1.0),
        ("POSITION: We should do this.", 1.0),
        ("POSITION: I am for it.", 1.0),
        ("POSITION: Support, favor, agree, endorse.", 1.0),    # clamped
        ("Body text.\nposition: I reject the proposal.\nMore text.", -1.0),
        ("No position tag here, I support it.", 0.0),
    ],
)
def test_position_polarity_matches_whole_words(text, expected):
    assert position_polarity(text) == expected


def test_presets_live_inside_the_package_so_a_wheel_ships_them():
    import agora
    package = Path(agora.__file__).resolve().parent
    assert personas.PERSONAS_DIR.parent == package
    assert "investment_styles" in personas.list_presets()
