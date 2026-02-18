"""Main CLI entry point for agora."""

from __future__ import annotations

import os
import sys

import click
from dotenv import load_dotenv
from rich.console import Console

from agora.personas import list_presets, load_preset, make_neutral_agents, parse_agent_spec
from agora.debate import run_debate

console = Console()


@click.group()
@click.version_option(package_name="agora-debate")
def cli():
    """agora — Multi-agent debate framework powered by Claude."""
    load_dotenv()


@cli.command()
@click.option("--topic", required=True, help="The debate topic or question.")
@click.option("--agents", default="3", help="Comma-separated agent names or a number for neutral agents.")
@click.option("--rounds", default=3, type=int, help="Number of debate rounds.")
@click.option("--preset", default=None, help="Use a built-in persona preset (e.g. investor_panel).")
@click.option("--model", default="sonnet", help="Model to use: haiku ($0.01), sonnet ($0.10), opus ($1.00).")
@click.option("--output", default="reports", help="Directory to save the report.")
@click.option("--no-stream", is_flag=True, help="Disable streaming output.")
def run(topic: str, agents: str, rounds: int, preset: str | None, model: str, output: str, no_stream: bool):
    """Run a multi-agent debate on a topic."""
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY not set.")
        console.print("Set it in your environment or create a .env file.")
        sys.exit(1)

    # Warnings
    if rounds > 10:
        console.print("[bold yellow]Warning:[/bold yellow] More than 10 rounds may be slow and expensive.")
        if not click.confirm("Continue?"):
            sys.exit(0)

    # Resolve agent configs
    if preset:
        try:
            data = load_preset(preset)
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
        agent_configs = data["agents"]
    else:
        parsed = parse_agent_spec(agents)
        if parsed is None:
            count = int(agents)
            if count > 8:
                console.print("[bold yellow]Warning:[/bold yellow] More than 8 agents may be slow and expensive.")
                if not click.confirm("Continue?"):
                    sys.exit(0)
            agent_configs = make_neutral_agents(count)
        else:
            if len(parsed) > 8:
                console.print("[bold yellow]Warning:[/bold yellow] More than 8 agents may be slow and expensive.")
                if not click.confirm("Continue?"):
                    sys.exit(0)
            agent_configs = parsed

    run_debate(topic, agent_configs, rounds=rounds, model=model, output_dir=output, stream=not no_stream)


@cli.command(name="presets")
def list_presets_cmd():
    """List available persona presets."""
    presets = list_presets()
    if not presets:
        console.print("[dim]No presets found.[/dim]")
        return
    console.print("[bold]Available presets:[/bold]")
    for name in presets:
        data = load_preset(name)
        agents_str = ", ".join(a["name"] for a in data.get("agents", []))
        console.print(f"  [cyan]{name}[/cyan] — {data.get('name', name)} ({agents_str})")


def main():
    cli()


if __name__ == "__main__":
    main()
