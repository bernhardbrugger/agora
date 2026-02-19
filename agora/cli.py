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
  OpenAI: gpt4o (default), gpt4o-mini, o1, o3-mini
  Gemini: flash (default), pro, thinking
  Grok: grok (default), grok-mini"""


@click.group()
@click.version_option(package_name="agora-debate")
def cli():
    """agora - Multi-agent debate framework powered by AI."""
    load_dotenv()


@cli.command()
@click.option("--topic", required=True, help="The debate topic or question.")
@click.option("--agents", default="3", help="Comma-separated agent names or a number for neutral agents.")
@click.option("--rounds", default=3, type=int, help="Number of debate rounds.")
@click.option("--preset", default=None, help="Use a built-in persona preset (e.g. investor_panel).")
@click.option("--provider", default="anthropic", help=PROVIDER_HELP)
@click.option("--model", default=None, help=MODEL_HELP)
@click.option("--output", default="reports", help="Directory to save the report.")
@click.option("--no-stream", is_flag=True, help="Disable streaming output.")
def run(topic: str, agents: str, rounds: int, preset: Optional[str], provider: str, model: Optional[str], output: str, no_stream: bool):
    """Run a multi-agent debate on a topic."""
    # Validate provider early with helpful error
    try:
        from agora.providers.base import LLMProvider
        LLMProvider.resolve(provider, model=model)
    except EnvironmentError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ImportError as e:
        console.print(f"[bold red]Missing dependency:[/bold red] {e}")
        console.print("Install it with: pip install <package>")
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

    run_debate(
        topic,
        agent_configs,
        rounds=rounds,
        model=model,
        provider_name=provider,
        output_dir=output,
        stream=not no_stream,
    )


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
        console.print(f"  [cyan]{name}[/cyan] - {data.get('name', name)} ({agents_str})")


@cli.command(name="providers")
def list_providers_cmd():
    """List available LLM providers and their models."""
    console.print("[bold]Available providers:[/bold]\n")
    providers = [
        ("anthropic", "ANTHROPIC_API_KEY", "Claude", "haiku, sonnet*, opus"),
        ("openai", "OPENAI_API_KEY", "GPT", "gpt4o*, gpt4o-mini, o1, o3-mini"),
        ("gemini", "GOOGLE_API_KEY", "Gemini", "flash*, pro, thinking"),
        ("grok", "XAI_API_KEY", "Grok", "grok*, grok-mini"),
    ]
    for name, env_var, display, models in providers:
        has_key = bool(os.environ.get(env_var))
        status = "[green]ready[/green]" if has_key else f"[red]needs {env_var}[/red]"
        console.print(f"  [cyan]{name:12s}[/cyan] {display:8s} {status}")
        console.print(f"               Models: {models}  (* = default)")
        console.print()


def main():
    cli()


if __name__ == "__main__":
    main()
