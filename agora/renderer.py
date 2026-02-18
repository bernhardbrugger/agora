"""Rich terminal output for debates."""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule

console = Console()


def print_header(topic: str, agent_names: list[str], rounds: int, model: str = "sonnet") -> None:
    """Print the debate header."""
    console.print()
    console.print(Rule("[bold]🏛️ AGORA[/bold] — Multi-Agent Debate", style="bright_blue"))
    console.print()
    console.print(f"  [bold]Topic:[/bold]  {topic}")
    console.print(f"  [bold]Agents:[/bold] {', '.join(agent_names)}")
    console.print(f"  [bold]Rounds:[/bold] {rounds}")
    console.print(f"  [bold]Model:[/bold]  {model}")
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


def print_agent_response_stream(agent, topic: str, round_num: int, total_rounds: int, history: list[dict]) -> str:
    """Stream an agent's response with live updating panel. Returns full text."""
    collected = []

    try:
        with Live(
            Panel("[dim]thinking...[/dim]", title=f"[bold]{agent.name}[/bold]", border_style=agent.color, padding=(1, 2)),
            console=console,
            refresh_per_second=8,
        ) as live:
            for chunk in agent.respond_stream(topic, round_num, total_rounds, history):
                collected.append(chunk)
                text_so_far = "".join(collected)
                live.update(Panel(
                    Markdown(text_so_far),
                    title=f"[bold]{agent.name}[/bold]",
                    border_style=agent.color,
                    padding=(1, 2),
                ))
    except KeyboardInterrupt:
        console.print("\n  [dim]Debate interrupted.[/dim]")
        raise SystemExit(0)
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e)
        if "AuthenticationError" in error_type or "401" in error_str:
            console.print(f"  [bold red]Error:[/bold red] Invalid API key. Check your ANTHROPIC_API_KEY.")
            raise SystemExit(1)
        elif "NotFoundError" in error_type or "could not resolve" in error_str.lower():
            console.print(f"  [bold yellow]Warning:[/bold yellow] Model not available for streaming, falling back...")
            text = agent.respond(topic, round_num, total_rounds, history)
            print_agent_response(agent.name, text, agent.color)
            return text
        else:
            console.print(f"  [bold red]API Error:[/bold red] {error_type}: {error_str}")
            raise SystemExit(1)

    return "".join(collected)


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
