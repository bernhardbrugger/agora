"""Evidence cards from an MCP server (``agora run --mcp-server CMD --mcp-call TOOL``).

agora starts the server as a local stdio process, calls each named tool once with
the given JSON arguments before the debate begins, and turns every result into
one evidence card, numbered after the file cards. The debate itself never talks
to the server: speakers only see the cards, so a model cannot call tools.

Pick read-only tools (data lookups such as quantdesk or a RIS/parliament server).
agora cannot tell a read-only tool from one that changes something; it calls
exactly the tools you name, once each.

Like file cards, tool output is untrusted data: it is fenced in the prompt and
escaped by every renderer. Needs the optional ``mcp`` package (Python 3.10+):
``pip install "mcp>=1.2"``.
"""

from __future__ import annotations

import asyncio
import json
import shlex
import sys
from typing import Iterable

from agora.evidence import MAX_CARD_CHARS, MAX_CARDS, EvidenceError

CALL_TIMEOUT_SECONDS = 60


def parse_call(spec: str) -> tuple[str, dict]:
    """``"tool"`` or ``'tool {"key": "value"}'`` -> (tool, arguments)."""
    spec = spec.strip()
    if not spec:
        raise EvidenceError("--mcp-call needs a tool name")
    name, _, raw_args = spec.partition(" ")
    raw_args = raw_args.strip()
    if not raw_args:
        return name, {}
    try:
        arguments = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"--mcp-call {name}: arguments are not valid JSON ({exc.msg})") from None
    if not isinstance(arguments, dict):
        raise EvidenceError(f"--mcp-call {name}: arguments must be a JSON object")
    return name, arguments


def split_command(command: str) -> list[str]:
    """Split the server command line the way the user's shell would."""
    parts = shlex.split(command, posix=sys.platform != "win32")
    parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in parts]
    if not parts:
        raise EvidenceError("--mcp-server needs a command")
    return parts


def _field(result, snake: str, camel: str):
    """A result field under its mcp 2.x (snake_case) or 1.x (camelCase) name."""
    value = getattr(result, snake, None)
    return getattr(result, camel, None) if value is None else value


def _result_text(result) -> str:
    """The text of a tool result: its text blocks, else its structured content as JSON."""
    texts = [block.text for block in getattr(result, "content", None) or [] if getattr(block, "type", "") == "text"]
    text = "\n".join(t for t in texts if t).strip()
    structured = _field(result, "structured_content", "structuredContent")
    if not text and structured is not None:
        text = json.dumps(structured, ensure_ascii=False, indent=2)
    return text


async def _call_tools(argv: list[str], calls: list[tuple[str, dict]]) -> list[tuple[str, dict, str]]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=argv[0], args=argv[1:])
    out: list[tuple[str, dict, str]] = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for name, arguments in calls:
                result = await session.call_tool(name, arguments)
                text = _result_text(result)
                if _field(result, "is_error", "isError"):
                    raise EvidenceError(f"MCP tool {name} returned an error: {text[:300] or 'no message'}")
                if not text:
                    raise EvidenceError(f"MCP tool {name} returned no text")
                out.append((name, arguments, text))
    return out


def load_mcp_evidence(server: str, call_specs: Iterable[str], first_number: int = 1) -> list[dict]:
    """Call each tool once and return cards ``{"id", "title", "text", "truncated"}``.

    Card ids start at ``E{first_number}`` so they follow the file cards.
    """
    calls = [parse_call(spec) for spec in call_specs]
    if not calls:
        return []
    if not server:
        raise EvidenceError("--mcp-call needs --mcp-server")
    if first_number - 1 + len(calls) > MAX_CARDS:
        raise EvidenceError(f"at most {MAX_CARDS} evidence cards in total, got {first_number - 1 + len(calls)}")
    argv = split_command(server)
    try:
        import mcp  # noqa: F401
    except ImportError:
        raise EvidenceError(
            'MCP evidence needs the mcp package (Python 3.10+): pip install "mcp>=1.2"'
        ) from None
    try:
        results = asyncio.run(asyncio.wait_for(_call_tools(argv, calls), CALL_TIMEOUT_SECONDS))
    except EvidenceError:
        raise
    except asyncio.TimeoutError:
        raise EvidenceError(f"MCP server did not answer within {CALL_TIMEOUT_SECONDS} s: {server}") from None
    except Exception as exc:  # the SDK wraps start-up and protocol failures in several types
        inner = _innermost(exc)
        if isinstance(inner, EvidenceError):  # our own message, re-raised through anyio's task group
            raise inner from None
        raise EvidenceError(f"MCP server {server!r} failed: {inner or type(inner).__name__}") from None

    cards: list[dict] = []
    for number, (name, arguments, text) in enumerate(results, start=first_number):
        title = f"mcp: {name}" + (f" {json.dumps(arguments, ensure_ascii=False, sort_keys=True)}" if arguments else "")
        cards.append({
            "id": f"E{number}",
            "title": title,
            "text": text[:MAX_CARD_CHARS],
            "truncated": len(text) > MAX_CARD_CHARS,
        })
    return cards


def _innermost(exc: BaseException) -> BaseException:
    """The first leaf of an exception group (anyio task groups wrap errors in one)."""
    while getattr(exc, "exceptions", None):
        exc = exc.exceptions[0]
    return exc
