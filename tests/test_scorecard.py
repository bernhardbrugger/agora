"""The debate scorecard: stance shifts and repeated arguments, from the transcript."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from agora.cli import cli
from agora.scorecard import build_scorecard, crux, scorecard_markdown, sources, stance, steelman, unsupported

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
    assert "| Ana | for → against → against | 1 | yes (for → against) | 1 | 0 | 0 |" in md
    assert "| Ben | against → - → against | 0 | no | 0 | 0 | 0 |" in md
    assert "**Changed position:** Ana." in md
    assert "No speaker cited a source." in md


def test_nobody_moved():
    t = _transcript()
    t["rounds"] = t["rounds"][:1]
    assert "**Changed position:** nobody." in scorecard_markdown(build_scorecard(t))


def test_sources_are_listed_once_in_order_without_the_position_line():
    text = (
        "Fares cover 40% of costs [source: Wiener Linien annual report 2024]. "
        "Ridership doubled [source:  Statistik  Austria ]. "
        "As said, 40% of costs [source: Wiener Linien annual report 2024].\n\n"
        "POSITION: I support it."
    )
    assert sources(text) == ["Wiener Linien annual report 2024", "Statistik Austria"]
    assert unsupported(text) == 0


@pytest.mark.parametrize("sentence", [
    "Fares cover 40% of the running costs.",
    "Congestion costs the city 2.5 billion a year.",
    "A recent study proved the opposite.",
    "According to the ministry, traffic fell.",
    "The data shows a clear decline.",
    "Prices rose 3 times faster than wages.",
])
def test_a_figure_or_a_study_without_a_source_is_unsupported(sentence):
    assert unsupported(sentence) == 1
    assert unsupported(sentence[:-1] + " [source: City budget 2025].") == 0


@pytest.mark.parametrize("sentence", [
    "I disagree with Ana on round 2 of this argument.",
    "Our data is thin, so I stay cautious.",
    "In 2019 the plan was first proposed.",
])
def test_plain_sentences_are_not_claims(sentence):
    assert unsupported(sentence) == 0


def test_every_speaker_is_told_how_to_cite():
    from agora.agent import Agent
    from agora.providers.dryrun import DryRunProvider

    prompt = Agent("Ana", "a sceptic", provider=DryRunProvider())._build_system_prompt(1, 3, "opening")
    assert "[source: <publication, organisation or URL>]" in prompt
    assert "Never invent a source." in prompt


def test_a_cue_only_in_the_position_line_does_not_count():
    assert unsupported("I stay where I was.\n\nPOSITION: I oppose it because 60% of riders disagree.") == 0


def test_scorecard_counts_sources_and_unsupported_claims_per_speaker():
    t = _transcript()
    t["rounds"][0]["turns"][1]["text"] = (
        "Fares cover 40% of costs [source: City budget 2025]. A study found more. POSITION: I oppose it."
    )
    t["rounds"][2]["turns"][1]["text"] = "Costs are 40% [source: City budget 2025]. POSITION: I oppose it."
    sc = build_scorecard(t)
    ana, ben = sc["agents"]
    assert (ana["sources"], ana["unsupported"]) == ([], 0)
    assert (ben["sources"], ben["unsupported"]) == (["City budget 2025"], 1)
    assert sc["unsupported"] == 1
    md = scorecard_markdown(sc)
    assert "| Ben | against → - → against | 0 | no | 0 | 1 | 1 |" in md
    assert "**Unsupported claims:** 1 sentence(s)" in md
    assert "### Evidence" in md and "- **Ben:** City budget 2025" in md
    assert "agora did not open or check them" in md


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


@pytest.mark.parametrize("line", [
    "STEELMAN: Ben is right that fares alone cannot fund the network.",
    "**STEELMAN:** Ben is right that fares alone cannot fund the network.",
    "  steelman: Ben is right that fares alone cannot fund the network.  ",
])
def test_steelman_line_is_found_with_or_without_emphasis(line):
    text = f"My argument stands.\n\n{line}\nPOSITION: I support it."
    assert steelman(text) == "Ben is right that fares alone cannot fund the network."


def test_no_steelman_line_or_an_empty_one_is_none():
    assert steelman("I steelman nobody here.\nPOSITION: I support it.") is None
    assert steelman("STEELMAN:\nPOSITION: I support it.") is None


def test_steelman_is_counted_from_round_two_per_speaker():
    t = _transcript()
    # round 1 has no steelman to ask for; one given in round 1 is not counted
    t["rounds"][0]["turns"][0]["text"] = "STEELMAN: early.\n" + t["rounds"][0]["turns"][0]["text"]
    t["rounds"][1]["turns"][0]["text"] = (
        "Something new.\nSTEELMAN: Ben fears 40% fare hikes.\nPOSITION: I oppose it."
    )
    sc = build_scorecard(t)
    ana, ben = sc["agents"]
    assert (ana["steelman_due"], ana["steelmen"]) == (2, [{"round": 2, "text": "Ben fears 40% fare hikes."}])
    assert (ben["steelman_due"], ben["steelmen"]) == (2, [])
    assert (sc["steelman_due"], sc["steelmen"]) == (4, 1)
    # the steelman restates the other side: not Ana's own unsupported claim
    assert ana["unsupported"] == 0
    md = scorecard_markdown(sc)
    # round 2 now says something new, so Ana has no repeat any more
    assert "| Ana | for → against → against | 1 | yes (for → against) | 0 | 0 | 0 | 1/2 | 0/3 |" in md
    assert "| Ben | against → - → against | 0 | no | 0 | 0 | 0 | 0/2 | 0/3 |" in md
    assert "1 of 4 turn(s) from round 2 on" in md
    assert "- **Ana** (round 2): Ben fears 40% fare hikes." in md


def test_a_repeated_steelman_is_not_a_repeat():
    line = "STEELMAN: Ana says rates matter more than earnings for every long duration asset we hold."
    t = {
        "agents": [{"name": "Cy", "role": ""}],
        "rounds": [{"number": n, "turns": [_turn("Cy", f"Short.\n{line}\nPOSITION: I oppose it.", "x", -1.0)]}
                   for n in (1, 2, 3)],
    }
    assert build_scorecard(t)["agents"][0]["repeats"] == 0


def test_one_round_asks_for_no_steelman():
    t = _transcript()
    t["rounds"] = t["rounds"][:1]
    md = scorecard_markdown(build_scorecard(t))
    assert "| - |" in md.splitlines()[6]
    assert "A one-round debate asks for no steelman." in md


def test_speakers_are_asked_for_a_steelman_from_round_two():
    from agora.agent import Agent
    from agora.providers.dryrun import DryRunProvider

    agent = Agent("Ana", "a sceptic", provider=DryRunProvider())
    assert "STEELMAN: " not in agent._build_system_prompt(1, 3, "opening")
    assert "'STEELMAN: '" in agent._build_system_prompt(2, 3, "rebuttal")


@pytest.mark.parametrize("line", [
    "CRUX: Would fares cover the running costs without subsidies?",
    "**CRUX:** Would fares cover the running costs without subsidies?",
    "> crux : Would fares cover the running costs without subsidies?  ",
])
def test_crux_line_is_found_with_or_without_emphasis(line):
    text = f"My argument stands.\n{line}\nPOSITION: I support it."
    assert crux(text) == "Would fares cover the running costs without subsidies?"


def test_no_crux_line_or_an_empty_one_is_none():
    assert crux("The crux of it is cost.\nPOSITION: I support it.") is None
    assert crux("CRUX:\nPOSITION: I support it.") is None


def test_cruxes_are_counted_every_turn_and_the_latest_is_listed():
    t = _transcript()
    t["rounds"][0]["turns"][0]["text"] = "CRUX: Do 30% of trips start downtown?\n" + t["rounds"][0]["turns"][0]["text"]
    t["rounds"][2]["turns"][0]["text"] += "\nCRUX: Will margins hold at 40% if prices fall?"
    t["rounds"][2]["turns"][1]["text"] = "CRUX: Who pays for maintenance?\nPOSITION: I oppose it."
    sc = build_scorecard(t)
    ana, ben = sc["agents"]
    assert (ana["crux_due"], [c["round"] for c in ana["cruxes"]]) == (3, [1, 3])
    assert (ben["crux_due"], ben["cruxes"]) == (3, [{"round": 3, "text": "Who pays for maintenance?"}])
    assert (sc["crux_due"], sc["cruxes"]) == (6, 3)
    # a crux is a question, not a claim: its figures are not unsupported
    assert ana["unsupported"] == 0
    md = scorecard_markdown(sc)
    assert md.splitlines()[6].endswith("| 2/3 |") and md.splitlines()[7].endswith("| 1/3 |")
    assert "3 of 6 turn(s) named, in a `CRUX:` line" in md
    cruxes = md.split("### Cruxes", 1)[1]
    assert "- **Ana** (round 3): Will margins hold at 40% if prices fall?" in cruxes
    assert "Do 30% of trips start downtown?" not in cruxes  # only the latest one per speaker
    assert "- **Ben** (round 3): Who pays for maintenance?" in cruxes


def test_a_repeated_crux_is_not_a_repeat():
    line = "CRUX: Do rates matter more than earnings for every long duration asset we hold?"
    t = {
        "agents": [{"name": "Cy", "role": ""}],
        "rounds": [{"number": n, "turns": [_turn("Cy", f"Short.\n{line}\nPOSITION: I oppose it.", "x", -1.0)]}
                   for n in (1, 2)],
    }
    assert build_scorecard(t)["agents"][0]["repeats"] == 0


def test_no_crux_named():
    md = scorecard_markdown(build_scorecard(_transcript()))
    assert "0 of 6 turn(s) named" in md and "No speaker named a crux." in md


def test_speakers_are_asked_for_a_crux_every_round():
    from agora.agent import Agent
    from agora.providers.dryrun import DryRunProvider

    agent = Agent("Ana", "a sceptic", provider=DryRunProvider())
    assert "'CRUX: '" in agent._build_system_prompt(1, 3, "opening")
    assert "'CRUX: '" in agent._build_system_prompt(3, 3, "closing")
