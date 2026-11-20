"""The debate scorecard: stance shifts and repeated arguments, from the transcript."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.scorecard import build_scorecard, scorecard_markdown, stance

LONG = "Rates matter more than earnings for long duration assets in every cycle we have seen."


def _turn(agent, text, position, polarity):
    return {"agent": agent, "text": text, "position": position, "polarity": polarity}


def _transcript():
    return {
        "agents": [{"name": "Ana", "role": ""}, {"name": "Ben", "role": ""}],
        "rounds": [
            {"number": 1, "turns": [
                _turn("Ana", f"{LONG}\n\nPOSITION: I support it.", "I support it.", 1.0),
                _turn("Ben", "Short. POSITION: I oppose it.", "I oppose it.", -1.0),
            ]},
            {"number": 2, "turns": [
                # the same sentence with one word changed: still a repeat
                _turn("Ana", LONG.replace("every", "each") + "\n\nPOSITION: I oppose it.", "I oppose it.", -1.0),
                # no POSITION line: no stance this round
                _turn("Ben", "I need more data before I say anything here.", None, 0.0),
            ]},
            {"number": 3, "turns": [
                _turn("Ana", "Something entirely new about margins and pricing power this time around.\n\nPOSITION: I oppose it.", "I oppose it.", -1.0),
                _turn("Ben", "POSITION: I oppose it.", "I oppose it.", -1.0),
            ]},
        ],
    }


def test_stance_from_polarity():
    assert (stance(0.5), stance(-1.0), stance(0.0)) == ("for", "against", "neutral")


def test_shifts_and_moved():
    sc = build_scorecard(_transcript())
    ana, ben = sc["agents"]
    assert ana["stances"] == ["for", "against", "against"]
    assert (ana["shifts"], ana["moved"], ana["opening"], ana["closing"]) == (1, True, "for", "against")
    # a round without a POSITION line is not a change of mind
    assert ben["stances"] == ["against", None, "against"]
    assert (ben["shifts"], ben["moved"]) == (0, False)
    assert sc["moved"] == ["Ana"]


def test_repeats_count_near_duplicates_only():
    sc = build_scorecard(_transcript())
    ana, ben = sc["agents"]
    assert ana["repeats"] == 1          # round 2 restates round 1; round 3 is new
    assert ben["repeats"] == 0          # short sentences and POSITION lines never count
    assert sc["repeats"] == 1


def test_position_lines_and_short_sentences_are_not_repeats():
    position = "POSITION: I support the plan because the costs fall every single year."
    text = f"I agree with that point.\n\n{position}"
    t = {
        "agents": [{"name": "Cy", "role": ""}],
        "rounds": [
            {"number": n, "turns": [_turn("Cy", text, position[10:], 1.0)]} for n in (1, 2, 3)
        ],
    }
    assert build_scorecard(t)["agents"][0]["repeats"] == 0


def test_markdown_names_who_moved_and_says_what_it_scores():
    md = scorecard_markdown(build_scorecard(_transcript()))
    assert md.startswith("## Scorecard")
    assert "It scores the debate, not the truth of the topic." in md
    assert "| Ana | for → against → against | 1 | yes (for → against) | 1 |" in md
    assert "| Ben | against → - → against | 0 | no | 0 |" in md
    assert "**Changed position:** Ana." in md


def test_nobody_moved():
    t = _transcript()
    t["rounds"] = t["rounds"][:1]
    assert "**Changed position:** nobody." in scorecard_markdown(build_scorecard(t))


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("agora.cli.load_dotenv", lambda *a, **k: None)


def test_dry_run_report_ends_with_the_scorecard(tmp_path):
    result = CliRunner().invoke(
        cli, ["run", "--dry-run", "--topic", "Is the thesis sound?", "--rounds", "3",
              "--output", str(tmp_path), "--no-stream"],
    )
    assert result.exit_code == 0, result.output
    report = next(tmp_path.glob("debate_*.md")).read_text(encoding="utf-8")
    assert report.index("# Moderator Synthesis") < report.index("## Scorecard")
    # the canned speakers alternate support/oppose and all close on support
    assert "**Changed position:**" in report and "nobody" not in report.split("## Scorecard")[1]
