# Changelog

All notable changes to agora. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
No version has been tagged or published to PyPI yet; the versions below are the ones set in `setup.py`,
reconstructed from the git history.

## [Unreleased]

### Added
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
