"""Rich terminal output for debates."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich.table import Table

console = Console()

# ── Phase metadata ────────────────────────────────────────────────────────────

_PHASE_LABELS: dict[str, str] = {
    "opening": "🎤 Opening Statement",
    "rebuttal": "⚔️  Rebuttal",
    "cross_examination": "🔍 Cross-Examination",
    "closing": "🏁 Closing Argument",
}

_PHASE_COLORS: dict[str, str] = {
    "opening": "bright_blue",
    "rebuttal": "bright_red",
    "cross_examination": "bright_yellow",
    "closing": "bright_green",
}


# ── Header ────────────────────────────────────────────────────────────────────

def print_header(
    topic: str,
    agent_names: list[str],
    rounds: int,
    model: str = "sonnet",
) -> None:
    """Print the debate header with structured metadata."""
    console.print()
    console.print(Rule(
        "[bold]🏛️  AGORA[/bold] — Structured Multi-Agent Debate",
        style="bright_blue",
    ))
    console.print()

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold dim", justify="right")
    grid.add_column()
    grid.add_row("Topic", f"[bold]{topic}[/bold]")
    grid.add_row("Participants", ", ".join(agent_names))
    grid.add_row("Rounds", str(rounds))
    grid.add_row("Model", model)
    console.print(grid)

    console.print()
    console.print(Rule(style="bright_blue"))
    console.print()


# ── Round / phase headers ─────────────────────────────────────────────────────

def print_round_header(round_num: int, total_rounds: int, phase: str = "rebuttal") -> None:
    """Print a round separator that includes the current debate phase."""
    label = _PHASE_LABELS.get(phase, phase.upper())
    color = _PHASE_COLORS.get(phase, "dim")
    console.print()
    console.print(Rule(
        f"[bold]Round {round_num} of {total_rounds}[/bold]  ·  [{color}]{label}[/{color}]",
        style="dim",
    ))
    console.print()


# ── Agent responses ───────────────────────────────────────────────────────────

def _agent_panel_title(agent_name: str, phase: str) -> str:
    label = _PHASE_LABELS.get(phase, "")
    title = f"[bold]{agent_name}[/bold]"
    if label:
        title += f"  [dim]{label}[/dim]"
    return title


def print_agent_response(
    agent_name: str,
    text: str,
    color: str = "white",
    phase: str = "",
) -> None:
    """Print an agent's response in a styled panel."""
    console.print(Panel(
        Markdown(text),
        title=_agent_panel_title(agent_name, phase),
        border_style=color,
        padding=(1, 2),
    ))


def print_agent_response_stream(
    agent,
    topic: str,
    round_num: int,
    total_rounds: int,
    history: list[dict],
    phase: str = "rebuttal",
    moderator_prompt: Optional[str] = None,
) -> str:
    """
    Stream an agent's response with a live-updating panel.
    Returns the full collected text.
    """
    collected: list[str] = []
    title = _agent_panel_title(agent.name, phase)

    try:
        with Live(
            Panel(
                "[dim]composing...[/dim]",
                title=title,
                border_style=agent.color,
                padding=(1, 2),
            ),
            console=console,
            refresh_per_second=10,
        ) as live:
            for chunk in agent.respond_stream(
                topic, round_num, total_rounds, history, phase, moderator_prompt
            ):
                collected.append(chunk)
                live.update(Panel(
                    Markdown("".join(collected)),
                    title=title,
                    border_style=agent.color,
                    padding=(1, 2),
                ))
    except KeyboardInterrupt:
        console.print("\n  [dim]Debate interrupted.[/dim]")
        raise SystemExit(0)
    except Exception as exc:
        etype = type(exc).__name__
        emsg = str(exc)
        if "AuthenticationError" in etype or "401" in emsg:
            console.print(
                "  [bold red]Error:[/bold red] Invalid API key. "
                "Check your ANTHROPIC_API_KEY."
            )
            raise SystemExit(1)
        elif "NotFoundError" in etype or "could not resolve" in emsg.lower():
            console.print(
                "  [bold yellow]Warning:[/bold yellow] "
                "Model unavailable for streaming — falling back to non-streaming."
            )
            text = agent.respond(topic, round_num, total_rounds, history, phase, moderator_prompt)
            print_agent_response(agent.name, text, agent.color, phase)
            return text
        else:
            console.print(f"  [bold red]API Error:[/bold red] {etype}: {emsg}")
            raise SystemExit(1)

    return "".join(collected)


# ── Moderator UI ──────────────────────────────────────────────────────────────

def print_thinking(name: str) -> None:
    """Show a brief 'thinking' indicator."""
    console.print(f"  [dim]⏳ {name} is thinking...[/dim]")


def print_moderator_intervention(prompt: str, round_num: int) -> None:
    """Display a moderator intervention before a round begins."""
    console.print()
    console.print(Panel(
        f"[italic]{prompt}[/italic]",
        title=f"[bold bright_yellow]🏛️  Moderator Intervention — Round {round_num}[/bold bright_yellow]",
        border_style="bright_yellow",
        padding=(1, 2),
    ))
    console.print()


def print_moderator_synthesis(text: str) -> None:
    """Display the moderator's final synthesis."""
    console.print()
    console.print(Rule(
        "[bold bright_yellow]🏛️  MODERATOR SYNTHESIS[/bold bright_yellow]",
        style="bright_yellow",
    ))
    console.print()
    console.print(Panel(
        Markdown(text),
        title="[bold bright_yellow]Final Analysis & Recommendation[/bold bright_yellow]",
        border_style="bright_yellow",
        padding=(1, 2),
    ))


# ── Consensus meter ───────────────────────────────────────────────────────────

def print_consensus_meter(
    score: float,
    round_num: int,
    all_scores: Optional[list[float]] = None,
) -> None:
    """Print a visual consensus bar with trend tracking."""
    pct = int(score * 100)

    if pct < 25:
        color, label = "red", "Strong Disagreement"
    elif pct < 45:
        color, label = "yellow", "Divergent Positions"
    elif pct < 65:
        color, label = "dark_orange", "Mixed Positions"
    elif pct < 80:
        color, label = "green", "Emerging Consensus"
    else:
        color, label = "bright_green", "High Consensus"

    filled = pct // 2
    bar = "█" * filled + "░" * (50 - filled)

    console.print()
    console.print(f"  [bold]Consensus Meter (Round {round_num}):[/bold]")
    console.print(f"  [{color}]{bar}[/{color}] {pct}% — {label}")

    if all_scores and len(all_scores) >= 2:
        delta = all_scores[-1] - all_scores[-2]
        if delta > 0.03:
            trend = f"[green]▲ +{delta:.0%} (converging)[/green]"
        elif delta < -0.03:
            trend = f"[red]▼ {delta:.0%} (diverging)[/red]"
        else:
            trend = "[dim]→ stable[/dim]"
        history_bar = " ".join(f"{int(s * 100)}%" for s in all_scores)
        console.print(f"  Trend: {trend}  [{history_bar}]")

    console.print()


def print_convergence_notice(score: float) -> None:
    """Announce that convergence has been reached and a closing round will follow."""
    console.print()
    console.print(Panel(
        f"[bold green]Convergence threshold reached ({score:.0%} consensus).[/bold green]\n"
        "Advancing directly to closing arguments.",
        title="[bold]🎯 Convergence Detected[/bold]",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()


# ── Misc ──────────────────────────────────────────────────────────────────────

def print_saved(path: str) -> None:
    """Print the report save location."""
    console.print()
    console.print(
        f"  [bold green]✓[/bold green] Report saved: [underline]{path}[/underline]"
    )
    console.print()
