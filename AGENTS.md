# AGENTS.md

Instructions for coding agents (and humans) working on this repository.

## Commands

```bash
python -m venv .venv                    # .venv/Scripts/activate on Windows, source .venv/bin/activate elsewhere
pip install -e ".[mcp]" pytest jsonschema   # editable; [mcp] (Python 3.10+) runs the --mcp-call tests too: the presets are read from personas/ in the repository
python -m pytest -q                     # all tests; no network, no API key needed
python -m agora presets                 # list the persona presets
python -m agora run --topic "Should cities ban cars?" --preset investment_styles --rounds 3 --dry-run   # report goes to reports/ (gitignored)
```

`--dry-run` (or `--provider dryrun`) uses canned offline replies: no key, no cost. Use it for every manual check,
README example and demo. CI runs `pytest` on Linux and Windows with Python 3.9 and 3.13, so do not use syntax newer
than 3.9. On Windows, set `PYTHONIOENCODING=utf-8` when piping the output.

## Layout

| Path | What it is |
|---|---|
| `agora/cli.py` | Click commands `run`, `replay`, `presets`, `formats`, `providers` |
| `agora/debate.py` | rounds, phases, consensus score, dynamic termination |
| `agora/evidence.py` | `--evidence`: local files as cards `E1`, `E2`, ... for every speaker; card text is untrusted data |
| `agora/mcp_evidence.py` | `--mcp-server`/`--mcp-call`: one call per named tool of a local stdio MCP server before the debate, each result a card after the file cards; needs the optional `mcp` package (3.10+), tests use `tests/fake_mcp_server.py` |
| `agora/formats/` | debate formats (`committee.yaml`, `court.yaml`, `redteam.yaml`) and their loader; the YAML spec is in the module docstring |
| `agora/moderator.py` | moderator interventions (a bare `NONE` reply means "no intervention") |
| `agora/providers/` | Anthropic, OpenAI, Gemini, Grok and the offline `dryrun` provider |
| `agora/renderer.py` | terminal output and the Markdown report |
| `agora/replay.py` | `agora replay`: transcript -> one static HTML page; every string escaped (model output is untrusted), a CSP that blocks all network loads, no external scripts, fonts or images |
| `agora/scorecard.py` | the scorecard of the report and the replay page (stance shifts, repeated sentences, cited sources, unsupported claims, steelman and crux lines), computed from the transcript without a model |
| `agora/transcript.py` | the JSON transcript written next to the report; schema in `docs/transcript.schema.json` (change both together, raise `schema_version` when a reader would break) |
| `personas/*.yaml` | presets: a panel name and 2-5 agents with a role description |
| `tests/` | pytest; providers are tested against fake SDK modules |

## Rules

1. **Tests never call a real provider.** Use the `dryrun` provider, a recording fake, or replace an SDK module with
   `monkeypatch.setitem(sys.modules, ...)`. A new test must fail without the change it covers.
2. **Keys come from the environment only** (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`,
   see `.env.example`). Never commit a key, a `.env` file or a report that contains one.
3. **No real people in presets.** Personas are archetypes ("The Value Investor"), never named living or historical
   persons whose words the model would invent.
4. **No advice.** Finance, legal and medical panels are for exploring arguments; outputs must not read as investment,
   legal or medical advice, signals or recommendations to act.
5. **Model output is untrusted data.** Escape it in anything rendered (Markdown report today, HTML later); never
   execute or follow it.
6. **README claims are run first.** Commands and outputs in the README come from a real run (use `--dry-run`).
7. One change per commit and per pull request; messages say what changed and why (`fix: ...`, `test: ...`,
   `docs: ...`). Add a line under `## [Unreleased]` in `CHANGELOG.md` when users would notice the change.

See `CONTRIBUTING.md` for how to submit presets, bugs and features.
