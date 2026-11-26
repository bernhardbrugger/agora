"""agora as an MCP server (``agora mcp``): start a debate from Claude Desktop or any MCP client.

Three tools over stdio:

- ``list_presets``: the persona presets and their speakers
- ``list_formats``: the institutional formats (committee, court, redteam, parliament) with roles, rounds and disclaimer
- ``run_debate``: run one debate and return the Markdown report, with the paths of the report,
  the JSON transcript and (by default) the HTML replay page; optional ``evidence`` texts become
  evidence cards, as files do for ``agora run --evidence``

The debate runs exactly as ``agora run --no-stream`` would: same providers, same keys from the
environment, same files. stdout carries the MCP protocol, so the terminal output of the debate goes
to stderr (the client's server log). There is no interactive confirmation over MCP, so the limits
the CLI asks about (more than 12 rounds, more than 8 speakers) are hard limits here.

Files are written below the output directory given to ``agora mcp --output`` (default
``~/agora-reports``), because a desktop client often starts servers in a directory the user never
looks at. Needs the optional ``mcp`` package (Python 3.10+): ``pip install "mcp>=1.2"``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

MAX_ROUNDS = 12
MAX_AGENTS = 8
DEFAULT_OUTPUT = Path.home() / "agora-reports"


class DebateRequestError(ValueError):
    """A run_debate request that cannot run; the message is shown to the client as is."""


def presets_info() -> list[dict]:
    """Every preset as ``{"id", "name", "agents"}`` (speaker names in order)."""
    from agora.personas import list_presets, load_preset

    out = []
    for preset_id in list_presets():
        data = load_preset(preset_id)
        out.append({
            "id": preset_id,
            "name": data.get("name", preset_id),
            "agents": [a["name"] for a in data.get("agents", [])],
        })
    return out


def formats_info() -> list[dict]:
    """Every format as ``{"id", "name", "description", "rounds", "roles", "disclaimer"}``."""
    from agora.formats import list_formats, load_format

    out = []
    for fmt_id in list_formats():
        fmt = load_format(fmt_id)
        out.append({
            "id": fmt_id,
            "name": fmt["name"],
            "description": fmt["description"],
            "rounds": len(fmt["phases"]),
            "roles": [a["name"] for a in fmt["agents"]],
            "disclaimer": fmt["disclaimer"],
        })
    return out


def resolve_request(
    topic: str,
    preset: Optional[str] = None,
    format_id: Optional[str] = None,
    agents: str = "3",
    rounds: Optional[int] = None,
) -> tuple[list[dict], int, Optional[dict]]:
    """Check a request the way ``agora run`` does -> (agent configs, rounds, format or None).

    Raises DebateRequestError with a message meant for the person asking.
    """
    from agora.personas import load_preset, make_neutral_agents, parse_agent_spec

    if not topic or not topic.strip():
        raise DebateRequestError("topic must not be empty")
    if preset and format_id:
        raise DebateRequestError("use either preset or format, not both")

    debate_format = None
    if format_id:
        from agora.formats import FormatError, load_format

        try:
            debate_format = load_format(format_id)
        except (FileNotFoundError, FormatError) as exc:
            raise DebateRequestError(str(exc)) from None
        fixed = len(debate_format["phases"])
        if rounds is not None and rounds != fixed:
            raise DebateRequestError(f"the {format_id} format has {fixed} rounds; leave out rounds")
        rounds = fixed
        agent_configs = debate_format["agents"]
    else:
        if rounds is None:
            rounds = 5
        if preset:
            try:
                agent_configs = load_preset(preset)["agents"]
            except FileNotFoundError as exc:
                raise DebateRequestError(str(exc)) from None
        else:
            parsed = parse_agent_spec(agents)
            if parsed is None:
                agent_configs = make_neutral_agents(int(agents))
            else:
                agent_configs = parsed

    if rounds < 2:
        raise DebateRequestError("rounds must be at least 2")
    if rounds > MAX_ROUNDS:
        raise DebateRequestError(f"rounds must be at most {MAX_ROUNDS} over MCP (long debates are slow and expensive)")
    if not agent_configs:
        raise DebateRequestError("agents must name at least one speaker")
    if len(agent_configs) > MAX_AGENTS:
        raise DebateRequestError(f"at most {MAX_AGENTS} speakers over MCP")
    return agent_configs, rounds, debate_format


def debate(
    topic: str,
    output_dir: Path,
    preset: Optional[str] = None,
    format_id: Optional[str] = None,
    agents: str = "3",
    rounds: Optional[int] = None,
    provider: str = "anthropic",
    model: Optional[str] = None,
    dry_run: bool = False,
    replay: bool = True,
    evidence: Optional[list[str]] = None,
) -> str:
    """Run one debate and return the text the client sees: file paths, then the full report."""
    from agora.debate import run_debate
    from agora.evidence import EvidenceError, cards_from_texts
    from agora.providers.base import LLMProvider

    if dry_run:
        provider, model = "dryrun", None
    agent_configs, rounds, debate_format = resolve_request(topic, preset, format_id, agents, rounds)
    try:
        cards = cards_from_texts(evidence or [])
    except EvidenceError as exc:
        raise DebateRequestError(str(exc)) from None
    try:
        LLMProvider.resolve(provider, model=model)
    except (EnvironmentError, ValueError, ImportError) as exc:
        raise DebateRequestError(str(exc)) from None

    report_path = Path(run_debate(
        topic=topic,
        agent_configs=agent_configs,
        rounds=rounds,
        model=model,
        provider_name=provider,
        output_dir=str(output_dir),
        stream=False,
        debate_format=debate_format,
        evidence=cards or None,
    ))
    lines = [f"Report: {report_path}", f"Transcript: {report_path.with_suffix('.json')}"]
    if replay:
        from agora.replay import write_replay

        lines.append(f"Replay: {write_replay(report_path.with_suffix('.json'))}")
    return "\n".join(lines) + "\n\n" + report_path.read_text(encoding="utf-8")


def build_server(output_dir: Path = DEFAULT_OUTPUT):
    """The MCP server object (mcp 2.x ``MCPServer`` or 1.x ``FastMCP``) with the three tools."""
    try:
        from mcp.server.mcpserver import MCPServer as Server
        from mcp.server.mcpserver.exceptions import ToolError
    except ImportError:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server
        from mcp.server.fastmcp.exceptions import ToolError

    server = Server(
        "agora",
        instructions=(
            "Structured multi-agent debates. Call list_presets or list_formats first, then run_debate. "
            "dry_run=true needs no API key and shows the flow with canned replies. Debates are for exploring "
            "arguments, never investment, legal or medical advice."
        ),
    )

    @server.tool()
    def list_presets() -> list[dict]:
        """List the persona presets (panels of 2-5 speakers) that run_debate accepts as `preset`."""
        return presets_info()

    @server.tool()
    def list_formats() -> list[dict]:
        """List the institutional formats (fixed roles, rounds and a disclaimer) that run_debate accepts as `format`."""
        return formats_info()

    @server.tool()
    def run_debate(
        topic: str,
        preset: Optional[str] = None,
        format: Optional[str] = None,
        agents: str = "3",
        rounds: Optional[int] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
        dry_run: bool = False,
        replay: bool = True,
        evidence: Optional[list[str]] = None,
    ) -> str:
        """Run a structured debate and return the Markdown report with the paths of report, transcript and replay.

        Use either `preset` or `format` (see list_presets / list_formats), or `agents`: a number of neutral
        speakers ("3") or comma-separated names ("CEO,CTO,CFO"). `rounds` defaults to 5 (formats fix their own).
        `provider` is anthropic, openai, gemini or grok and needs its API key in the server's environment;
        `dry_run` uses canned offline replies (no key, no cost). A real debate makes several model calls per
        round and can take minutes.

        `evidence`: up to 20 texts (facts, excerpts, tool results you already have) that every speaker gets as
        evidence cards E1, E2, ... to cite as [source: E1]; each is cut at 4000 characters and treated as data,
        never as instructions. The report lists the cards and flags citations of cards that do not exist.
        """
        try:
            return debate(
                topic, output_dir, preset, format, agents, rounds, provider, model, dry_run, replay, evidence
            )
        except DebateRequestError as exc:
            raise ToolError(str(exc)) from None

    return server


def serve(output_dir: Path = DEFAULT_OUTPUT) -> None:
    """Run the server on stdio; debate output goes to stderr so stdout stays the protocol channel."""
    from rich.console import Console

    from agora import renderer

    renderer.console = Console(stderr=True)
    build_server(Path(output_dir).expanduser()).run()
