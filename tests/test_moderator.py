"""Moderator: when an intervention counts as one, and what the model is asked."""

from __future__ import annotations

from typing import Iterator

import pytest

from agora.moderator import Moderator
from agora.providers.base import LLMProvider


class Recorder(LLMProvider):
    """Returns a fixed answer and keeps every call for inspection."""

    def __init__(self, answer: str):
        self.answer = answer
        self.calls: list[dict] = []

    def complete(self, system, messages, max_tokens=1024):
        self.calls.append({"system": system, "messages": messages, "max_tokens": max_tokens})
        return self.answer

    def stream(self, system, messages, max_tokens=1024) -> Iterator[str]:
        yield self.complete(system, messages, max_tokens)


HISTORY = [
    {"round": 1, "phase": "opening", "agent": "Ada", "text": "Cars should go."},
    {"round": 1, "phase": "opening", "agent": "Bo", "text": "Cars should stay."},
]


def _intervene(answer: str):
    llm = Recorder(answer)
    result = Moderator(provider=llm).generate_intervention(
        "Should cities ban cars?", HISTORY, ["Ada", "Bo"], round_num=2, consensus_score=0.42
    )
    return result, llm


@pytest.mark.parametrize("answer", ["NONE", "none", "  None.\n", "NONE!"])
def test_a_bare_none_means_no_intervention(answer):
    assert _intervene(answer)[0] is None


@pytest.mark.parametrize(
    "answer",
    [
        "None of you has said who pays for the buses. Who does?",
        "Nonetheless: what happens to deliveries?",
    ],
)
def test_a_question_that_starts_with_none_is_still_an_intervention(answer):
    assert _intervene(answer)[0] == answer


def test_an_intervention_is_returned_without_surrounding_whitespace():
    assert _intervene("\n  What about ambulances?  \n")[0] == "What about ambulances?"


def test_the_intervention_prompt_carries_topic_people_round_score_and_transcript():
    _, llm = _intervene("NONE")
    (call,) = llm.calls
    prompt = call["messages"][0]["content"]
    assert call["messages"][0]["role"] == "user"
    assert '"Should cities ban cars?"' in prompt
    assert "Participants: Ada, Bo" in prompt
    assert "Consensus score after last round: 42%" in prompt
    assert "introduce Round 2" in prompt
    assert "Cars should go." in prompt and "Cars should stay." in prompt
    assert call["max_tokens"] == 350


def test_synthesis_returns_the_model_text_and_shows_the_consensus_trend():
    llm = Recorder("## The Real Crux\nParking.")
    text = Moderator(provider=llm).synthesize(
        "Should cities ban cars?", HISTORY, ["Ada", "Bo"], [0.2, 0.355, 0.6]
    )
    assert text == "## The Real Crux\nParking."
    (call,) = llm.calls
    prompt = call["messages"][0]["content"]
    assert "Consensus trend across rounds: 20% → 36% → 60%" in prompt
    assert "## Final Recommendation" in prompt
    assert call["max_tokens"] == 3000
