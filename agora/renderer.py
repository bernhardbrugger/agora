"""Rich terminal output for debates."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich.markdown import Markdown
from rich.rule import Rule

console = Console()


def print_header(topic: str, agent_names: list[str], rounds: int) -> None:
    """Print the debate header."""
    console.print()
    console.print(Rule("[bold]AGORA[/bold] — Multi-Agent Debate", style="bright_blue"))
    console.print()
    console.print(f"  [bold]Topic:[/bold]  {topic}")
    console.print(f"  [bold]Agents:[/bold] {', '.join(agent_names)}")
    console.print(f"  [bold]Rounds:[/bold] {rounds}")
    console.print()
    console.print(Rule(style="bright_blue"))
    console.print()


def print_round_header(round_num: int, total_rounds: int) -> None:
    """Print a round separator."""
    console.print()
    console.print(Rule(f"[bold]Round {round_num} of {total_rounds}[/bold]", style="dim"))
    console.print()


def print_agent_response(agent_name: str, text: str, color: str = "white") -> None:
    """Print an agent's response in a colored panel."""
    console.print(Panel(
        Markdown(text),
        title=f"[bold]{agent_name}[/bold]",
        border_style=color,
        padding=(1, 2),
    ))


def print_thinking(agent_name: str) -> None:
    """Print a thinking indicator."""
    console.print(f"  [dim]⏳ {agent_name} is thinking...[/dim]")


def print_consensus_meter(score: float, round_num: int) -> None:
    """Print a consensus meter (0 = total disagreement, 1 = full consensus)."""
    pct = int(score * 100)

    if pct < 30:
        color = "red"
        label = "High Disagreement"
    elif pct < 60:
        color = "yellow"
        label = "Mixed Positions"
    else:
        color = "green"
        label = "Approaching Consensus"

    bar = "█" * (pct // 2) + "░" * (50 - pct // 2)
    console.print()
    console.print(f"  [bold]Consensus Meter (Round {round_num}):[/bold]")
    console.print(f"  [{color}]{bar}[/{color}] {pct}% — {label}")
    console.print()


def print_moderator_synthesis(text: str) -> None:
    """Print the moderator's final synthesis."""
    console.print()
    console.print(Rule("[bold bright_yellow]MODERATOR SYNTHESIS[/bold bright_yellow]", style="bright_yellow"))
    console.print()
    console.print(Panel(
        Markdown(text),
        title="[bold bright_yellow]🏛️  Moderator[/bold bright_yellow]",
        border_style="bright_yellow",
        padding=(1, 2),
    ))


def print_saved(path: str) -> None:
    """Print the save location."""
    console.print()
    console.print(f"  [bold green]✓[/bold green] Report saved to: [underline]{path}[/underline]")
    console.print()
