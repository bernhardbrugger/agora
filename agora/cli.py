"""Main CLI entry point for agora."""

from __future__ import annotations

import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console

from agora.personas import list_presets, load_preset, make_neutral_agents, parse_agent_spec
from agora.debate import run_debate

console = Console()

PROVIDER_HELP = """LLM provider to use:
  anthropic  — Claude (default). Needs ANTHROPIC_API_KEY
  openai     — GPT. Needs OPENAI_API_KEY
  gemini     — Google Gemini. Needs GOOGLE_API_KEY
  grok       — xAI Grok. Needs XAI_API_KEY"""

MODEL_HELP = """Model to use (provider-specific):
  Anthropic: haiku, sonnet (default), opus
  OpenAI:    gpt4o (default), gpt4o-mini, o1, o3-mini
  Gemini:    flash (default), pro, thinking
  Grok:      grok (default), grok-mini"""


@click.group()
@click.version_option(package_name="agora-debate")
def cli():
    """agora — Structured multi-agent debate framework powered by AI."""
    load_dotenv()


@cli.command()
@click.option(
    "--topic", required=True,
    help="The debate topic or question.",
)
@click.option(
    "--agents", default="3",
    help="Comma-separated agent names OR a number for neutral archetypes (e.g. '3' or 'CEO,CTO,CFO').",
)
@click.option(
    "--rounds", default=5, type=int,
    help="Number of debate rounds (default: 5). Minimum 3 recommended for full phase coverage.",
)
@click.option(
    "--preset", default=None,
    help="Use a built-in persona preset (e.g. investment_legends). Run 'agora presets' to list all.",
)
@click.option(
    "--provider", default="anthropic",
    help=PROVIDER_HELP,
)
@click.option(
    "--model", default=None,
    help=MODEL_HELP,
)
@click.option(
    "--output", default="reports",
    help="Directory to save the Markdown report (default: reports/).",
)
@click.option(
    "--no-stream", is_flag=True,
    help="Disable streaming output (show responses only after completion).",
)
@click.option(
    "--dynamic", is_flag=True, default=False,
    help="Dynamically terminate the debate when consensus is reached, adding a closing round.",
)
@click.option(
    "--convergence", default=0.75, type=float, show_default=True,
    help="Consensus score threshold for dynamic termination (0.0–1.0).",
)
@click.option(
    "--no-interventions", is_flag=True, default=False,
    help="Disable moderator interventions between rounds.",
)
def run(
    topic: str,
    agents: str,
    rounds: int,
    preset: Optional[str],
    provider: str,
    model: Optional[str],
    output: str,
    no_stream: bool,
    dynamic: bool,
    convergence: float,
    no_interventions: bool,
) -> None:
    """Run a structured multi-agent debate on any topic."""
    # Validate provider and API key early
    try:
        from agora.providers.base import LLMProvider
        LLMProvider.resolve(provider, model=model)
    except EnvironmentError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)
    except ImportError as exc:
        console.print(f"[bold red]Missing dependency:[/bold red] {exc}")
        console.print("Install it with: pip install <package>")
        sys.exit(1)

    if rounds > 12:
        console.print(
            f"[bold yellow]Warning:[/bold yellow] {rounds} rounds will make this "
            "debate long and expensive."
        )
        if not click.confirm("Continue?"):
            sys.exit(0)

    if rounds < 2:
        console.print("[bold red]Error:[/bold red] --rounds must be at least 2.")
        sys.exit(1)

    # ── Resolve agent configs ────────────────────────────────────────────
    if preset:
        try:
            data = load_preset(preset)
        except FileNotFoundError as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            sys.exit(1)
        agent_configs = data["agents"]
    else:
        parsed = parse_agent_spec(agents)
        if parsed is None:
            count = int(agents)
            if count > 8:
                console.print(
                    "[bold yellow]Warning:[/bold yellow] More than 8 agents may be slow and expensive."
                )
                if not click.confirm("Continue?"):
                    sys.exit(0)
            agent_configs = make_neutral_agents(count)
        else:
            if len(parsed) > 8:
                console.print(
                    "[bold yellow]Warning:[/bold yellow] More than 8 agents may be slow and expensive."
                )
                if not click.confirm("Continue?"):
                    sys.exit(0)
            agent_configs = parsed

    run_debate(
        topic=topic,
        agent_configs=agent_configs,
        rounds=rounds,
        model=model,
        provider_name=provider,
        output_dir=output,
        stream=not no_stream,
        dynamic=dynamic,
        convergence_threshold=convergence,
        moderator_interventions=not no_interventions,
    )


@cli.command(name="presets")
def list_presets_cmd() -> None:
    """List all available persona presets with their participants."""
    presets = list_presets()
    if not presets:
        console.print("[dim]No presets found.[/dim]")
        return
    console.print("[bold]Available presets:[/bold]")
    console.print()
    for name in presets:
        data = load_preset(name)
        agents_str = ", ".join(a["name"] for a in data.get("agents", []))
        console.print(f"  [cyan bold]{name}[/cyan bold] — {data.get('name', name)}")
        console.print(f"  [dim]  {agents_str}[/dim]")
        console.print()


@cli.command(name="providers")
def list_providers_cmd() -> None:
    """List available LLM providers and their models."""
    console.print("[bold]Available providers:[/bold]\n")
    providers = [
        ("anthropic", "ANTHROPIC_API_KEY", "Claude", "haiku, sonnet*, opus"),
        ("openai",    "OPENAI_API_KEY",    "GPT",    "gpt4o*, gpt4o-mini, o1, o3-mini"),
        ("gemini",    "GOOGLE_API_KEY",    "Gemini", "flash*, pro, thinking"),
        ("grok",      "XAI_API_KEY",       "Grok",   "grok*, grok-mini"),
    ]
    for name, env_var, display, models in providers:
        has_key = bool(os.environ.get(env_var))
        status = "[green]ready[/green]" if has_key else f"[red]needs {env_var}[/red]"
        console.print(f"  [cyan]{name:12s}[/cyan] {display:8s} {status}")
        console.print(f"               Models: {models}  (* = default)")
        console.print()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
