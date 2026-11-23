# Changelog

All notable changes to agora. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
No version has been tagged or published to PyPI yet; the versions below are the ones set in `setup.py`,
reconstructed from the git history.

## [Unreleased]

### Added
- Evidence from an MCP server: `agora run --mcp-server "CMD" --mcp-call 'TOOL {JSON}'` (repeatable) starts a local
  stdio MCP server, calls each named tool once before round 1 and turns every result into the next evidence card
  (`mcp: TOOL {args}`), numbered after the `--evidence` files and limited by the same 20 cards and 4,000 characters.
  Speakers see only the cards and cannot call tools. A tool error, an unknown tool or a server that does not start
  (60 s) stops the run with the tool's message. Optional extra `agora-debate[mcp]` (Python 3.10+); CI runs the tests
  against a fake stdio server in `tests/fake_mcp_server.py`.
- Evidence cards: `agora run --evidence FILE` (repeatable, up to 20 UTF-8 files, each cut at 4,000 characters) gives
  every speaker the files as cards `E1`, `E2`, ... with a rule to cite them as `[source: E1]`; the cards are fenced in
  the prompt and marked as data, not instructions. The report lists the cards, the transcript records them in an
  optional `evidence` field (schema updated, version unchanged), and the dry-run provider cites the first card.
  agora does not check that a citation matches the card. The replay page shows the cards as collapsible sections
  before the debate (anchor `#card-E1`), title and text escaped. A citation of a card id that was never given
  (`[source: E7]` with only `E1`-`E2`) is named in an `Unknown cards` line under the Evidence list, in the report and
  on the replay page.
- Crux check: every turn asks for one `CRUX:` sentence, the question of fact or value that would change the
  speaker's position; the report's scorecard shows per speaker how many turns had one (`given/asked`) and lists each
  speaker's latest crux. It checks presence, not quality, and does not match cruxes across speakers. `CRUX:` lines do
  not count as repeats or unsupported claims. The dry-run provider emits a placeholder crux line. The replay page shows
  the Crux column and Cruxes list too, each line escaped.
- Steelman check: from round 2 on, speakers are asked for one `STEELMAN:` sentence that states the other side's
  strongest argument; the report's scorecard shows per speaker how many of those turns had one (`given/asked`) and
  quotes them in a Steelman list. It checks presence, not quality. `STEELMAN:` lines do not count as repeats or
  unsupported claims. The dry-run provider emits a placeholder steelman line. The replay page shows the Steelman
  column and list too, each line escaped.
- Evidence in the report: speakers are told to cite figures, studies and statistics inline as `[source: ...]`; the
  scorecard counts each speaker's distinct sources and "unsupported" sentences (a figure or a study/statistic cue
  without a citation), and an Evidence list names what was cited. Sources are listed as claimed, never checked.
  The replay page shows the Sources and Unsupported columns and the Evidence list too, each source escaped and
  shown as text, never as a link.
- A scorecard at the end of every report, computed from the transcript without a model: each speaker's stance by
  round, how often it shifted, who changed position from opening to closing, and how many sentences restated the
  speaker's own earlier sentence. It scores the debate, not the truth of the topic. The replay page shows the
  same scorecard, derived from the transcript (so older transcripts get it too).
- Debate formats: `agora run --format committee` runs an investment committee (bull, bear, risk officer, quant,
  devil's advocate; 4 fixed phases) whose moderator writes a decision memo that keeps the dissent, with a
  "not investment advice" disclaimer in the terminal and the report. `agora formats` lists them; the YAML spec is
  in `agora/formats/__init__.py`, and formats ship inside the package. The transcript records the format
  (optional `format` field) and the replay page shows its name and disclaimer.
- `agora run --format court`: an educational moot court (prosecution, defence, neutral expert, juror) whose
  judge writes a judgment with the burden of proof applied, a verdict and the minority opinion; "not legal
  advice", fictional or historic public cases only.
- `agora run --format redteam`: a red-team review (plan owner, red team lead, pre-mortem analyst, mitigation
  engineer) whose report ranks the risks, lists mitigations with their remaining risk, keeps what survived and
  names tripwires; it critiques ideas, not people, and stays at design level (no exploit code or attack steps).
- `agora run --replay` writes the HTML replay page right after the debate, next to the report.
- `agora replay TRANSCRIPT.json [-o page.html]`: one self-contained HTML page with a position grid
  (for/against per agent and round, linked to the speech), the consensus per round, every speech, the
  moderator's interventions and the synthesis. It loads nothing from the network and escapes all model text.
- Every run also writes a JSON transcript next to the Markdown report (same name, `.json`): agents,
  rounds with phase, consensus score, moderator intervention and each turn's `POSITION:` and polarity, plus
  the synthesis. Documented as a JSON Schema in `docs/transcript.schema.json` (version 1).
- `agora run --dry-run` (same as `--provider dryrun`): a full debate offline with canned, deterministic
  answers, no API key and no cost.
- Tests (64) for debate phases, the consensus score, presets, agent specs, reports, the dry run, the
  moderator and the OpenAI/Gemini providers (against fake SDKs, no network); CI on Linux and Windows,
  Python 3.9 and 3.13.
- MIT `LICENSE` file (the README and `setup.py` already declared MIT).

### Changed
- The presets that put words in the mouths of real people were replaced by archetypes:
  `investment_styles`, `tech_builders`, `statecraft`, `science_archetypes`.
- README: a Limitations section, install instructions for the optional providers, and an honest
  account of what is tested.

### Fixed
- The moderator dropped every intervention whose text started with "None" ("None of you has said
  ..."); only a bare `NONE` now means no intervention.
- The consensus score matched position words inside other words; it now matches whole words.
- The terminal consensus meter truncated (46 %) while the saved report rounded (47 %); both round now.

## [0.4.0] - 2026-02-24

Includes everything that was briefly numbered 0.3.0 on the same day.

### Added
- Structured debate phases mapped to rounds: opening, rebuttal, cross-examination, closing.
- Active moderator: Socratic interventions when a debate stalls (`--no-interventions` turns them off)
  and an eight-section final synthesis.
- `--dynamic` and `--convergence`: skip to the closing round once the consensus threshold is met.
- Consensus trend across rounds; consensus weighs keyword overlap (60 %) and `POSITION:` polarity (40 %).
- Presets `ethics_panel`, `scientific_panel`, `legal_panel`, `medical_panel` (16 presets in total).

### Changed
- Every agent states a `POSITION:` sentence each round; token budget per turn raised from 1024 to 1500.
- Default rounds raised from 3 to 5; the existing presets were rewritten with fuller role descriptions.

### Fixed
- YAML escaping in four presets.

## [0.2.1] - 2026-02-19

### Added
- Providers for OpenAI, Google Gemini and xAI Grok besides Anthropic (`--provider`, optional extras).
- Presets `science_minds`, `world_leaders`, `product_design`, `crypto_council`.
- `python -m agora`.

### Fixed
- Python 3.9 compatibility (`Optional` instead of `X | None`) and UTF-8 reads of the README and presets.

## [0.2.0] - 2026-02-18

### Added
- Model selection (`--model`), live streaming panels (`--no-stream` to turn them off), consensus meter.
- Retries with backoff on rate limits; error handling for streaming, authentication and Ctrl+C.
- Presets `tech_legends`, `investment_legends`, `debate_club`; `CONTRIBUTING.md`.

## 0.1.0 - 2026-02-18

- First version: multi-agent debates on Anthropic models with presets and a Markdown report.
