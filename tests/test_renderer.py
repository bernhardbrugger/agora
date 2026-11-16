"""The terminal consensus meter must show the same numbers as the saved report."""

from __future__ import annotations

import io

from rich.console import Console

from agora import renderer


def _meter(monkeypatch, score, history=None):
    out = io.StringIO()
    monkeypatch.setattr(renderer, "console", Console(file=out, width=120, color_system=None))
    renderer.print_consensus_meter(score, len(history or [score]), history)
    return out.getvalue()


def test_meter_rounds_like_the_report(monkeypatch):
    # the report writes f"{0.466:.0%}" == "47%"; truncation would print 46%
    text = _meter(monkeypatch, 0.466, [0.30, 0.466])
    assert " 47% — Mixed Positions" in text
    assert "[30% 47%]" in text


def test_meter_band_and_bar_follow_the_rounded_percent(monkeypatch):
    # 0.799 rounds to 80%: the label and the bar must agree with the printed number
    text = _meter(monkeypatch, 0.799)
    assert "█" * 40 + "░" * 10 + " 80% — High Consensus" in text
