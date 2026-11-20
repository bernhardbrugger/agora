<div align="center">

# 🏛️ Agora

### *Structured multi-agent AI debates — with phases, active moderation, and real resolution*

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Multi-Provider](https://img.shields.io/badge/providers-Claude%20·%20GPT%20·%20Gemini%20·%20Grok-blueviolet.svg)](#-supported-providers)

**Agora** is a CLI tool that orchestrates high-quality multi-agent AI debates on any topic. Agents don't just take turns talking — they open, rebut, cross-examine, and close. An active moderator intervenes when the debate stalls. A synthesis analyst resolves the outcome with specific recommendations and unresolved cruxes.

[Features](#features) · [Installation](#installation) · [Quick Start](#-quick-start) · [How It Works](#how-it-works) · [Presets](#-presets) · [Advanced Usage](#advanced-usage) · [Troubleshooting](#-troubleshooting)

</div>

---

## Features

- 🎭 **16 Built-in Presets** — From investment styles to ethics panels to medical boards
- 🔄 **Structured Debate Phases** — Opening → Rebuttal → Cross-Examination → Closing, each with distinct argumentation rules
- 🏛️ **Active Moderation** — The moderator intervenes between rounds with Socratic challenges when the debate stalls or goes in circles
- 📍 **Position Tracking** — Every agent commits to an explicit position each round, making evolution visible
- 🎯 **Dynamic Termination** — Optionally halt early when consensus is reached and jump straight to closing arguments
- 📊 **Consensus Meter** — Visual agreement tracking with round-by-round trend arrows
- 🔍 **Deep Synthesis** — Final analysis covers the real crux, position evolution, common ground, unresolved cruxes, and a concrete recommendation
- 🌊 **Real-time Streaming** — Watch the debate unfold live in your terminal
- 🤖 **Multi-Provider** — Claude, GPT-4o, Gemini, or Grok

---

## 🤖 Supported Providers

| Provider | Flag | Models | API Key |
|----------|------|--------|---------|
| **Anthropic** (default) | `--provider anthropic` | `haiku`, `sonnet`*, `opus` | `ANTHROPIC_API_KEY` |
| **OpenAI** | `--provider openai` | `gpt4o`*, `gpt4o-mini`, `o1`, `o3-mini` | `OPENAI_API_KEY` |
| **Google Gemini** | `--provider gemini` | `flash`*, `pro`, `thinking` | `GOOGLE_API_KEY` |
| **xAI Grok** | `--provider grok` | `grok`*, `grok-mini` | `XAI_API_KEY` |

*\* = default model for that provider*

```bash
# Use Claude Sonnet (default)
agora run --topic "Your topic" --preset neutral

# Use GPT-4o
agora run --topic "Your topic" --preset neutral --provider openai

# Use Gemini Flash
agora run --topic "Your topic" --preset neutral --provider gemini --model flash

# Check which providers are configured
agora providers
```

Install optional provider dependencies (from your clone; Agora is not published on PyPI):
```bash
pip install -e ".[openai]"   # For OpenAI / Grok
pip install -e ".[gemini]"   # For Google Gemini
pip install -e ".[all]"      # Everything
```

---

## Installation

### macOS / Linux

```bash
git clone https://github.com/bernhardbrugger/agora.git
cd agora
pip install -e .
agora --help
```

### Windows

```bash
git clone https://github.com/bernhardbrugger/agora.git
cd agora
pip install -e .

# If 'agora' isn't recognised, use:
python -m agora run --topic "Your topic" --preset neutral
```

> **Windows tip:** If `agora` isn't found after install, use `python -m agora` as a reliable alternative.

### Requirements

- Python 3.9+
- An API key for your chosen provider (see table above)

---

## Setup

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-your-key"

# OpenAI
export OPENAI_API_KEY="sk-your-key"

# Google Gemini
export GOOGLE_API_KEY="your-key"

# xAI Grok
export XAI_API_KEY="your-key"
```

Or create a `.env` file in the project root — Agora will load it automatically.

---

## 🚀 Quick Start

Try the whole flow first without an API key and without cost. `--dry-run` uses canned offline replies: you see the phases, the moderator, the consensus meter and the saved report, but the text is placeholder text, not a debate.

```bash
agora run --dry-run --topic "Should cities ban cars from their centres?" --rounds 3
```

From that run (the speakers alternate between "support" and "oppose", then all close on "support"):

```
  Consensus Meter (Round 1):
  ███████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ 47% — Mixed Positions
  Consensus Meter (Round 2):
  ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 45% — Mixed Positions
  Consensus Meter (Round 3):
  ███████████████████████████████████████████░░░░░░░ 86% — High Consensus
```

With a key set, a real debate:

```bash
# Classic balanced debate — 5 structured rounds
agora run --topic "Should we colonize Mars?" --preset neutral

# Investment thesis from competing investment styles
agora run --topic "Is NVIDIA overvalued at current prices?" --preset investment_styles

# Ethics panel — 4 competing moral frameworks
agora run --topic "Should AI systems be allowed to make medical decisions?" --preset ethics_panel

# Science panel — empiricist vs. theorist vs. sceptic
agora run --topic "Is consciousness computable?" --preset scientific_panel

# Legal panel — advocate, judge, scholar, policy analyst
agora run --topic "Should social media platforms be liable for user content?" --preset legal_panel

# Medical board — clinician, epidemiologist, bioethicist, economist
agora run --topic "Should organ donation be opt-out by default?" --preset medical_panel

# Startup team — ground-level board meeting
agora run --topic "Should we pivot from B2C to B2B SaaS?" --preset startup_team

# Philosophers at war
agora run --topic "Is it ethical to lie to protect someone's feelings?" --preset philosophy

# Tech builders on product strategy
agora run --topic "Should our startup go open-source?" --preset tech_builders

# Quick pro/con — sharpest 2-agent format
agora run --topic "Should I quit my job to start a company?" --preset devils_advocate
```

---

## How It Works

### Debate Structure

Every debate flows through structured phases — not just open-ended rounds:

```
Round 1 ── Opening Statements
           Each agent stakes their thesis independently.

Round 2-N-2 ── Rebuttals
           Agents quote and counter specific opposing arguments.
           The moderator may inject a Socratic challenge if the
           debate stalls, repeats, or misses a critical dimension.

Round N-1 ── Cross-Examination  (debates with 4+ rounds)
           Agents pose targeted questions directly to named opponents,
           attacking inconsistencies and undefended assumptions.

Round N ── Closing Arguments
           Agents state their final, possibly evolved positions,
           acknowledge the strongest opposing point, and identify
           at least one area of common ground.
```

### Moderator Interventions

Before each round (from Round 2 on), the moderator analyses the transcript and decides whether to inject a challenge. It intervenes when:

- Agents are arguing past each other without genuine engagement
- A critical dimension of the topic has been entirely ignored
- Arguments are being repeated without development
- An unexamined assumption is driving the entire disagreement
- A concrete scenario or edge case would clarify the debate

### Consensus Tracking

After every round, Agora calculates a consensus score combining keyword overlap (Jaccard similarity) and position polarity alignment (from the `POSITION:` sentence each agent must include). The meter shows trends across rounds:

```
Consensus Meter (Round 3):
████████████████████████░░░░░░░░░░ 47% — Mixed Positions
Trend: ▲ +12% (converging)  [24% → 35% → 47%]
```

### Moderator Synthesis

The final synthesis covers eight structured sections:

| Section | What it answers |
|---------|----------------|
| **The Real Crux** | The fundamental disagreement driving everything |
| **Strongest Arguments FOR/AGAINST** | Best-quality arguments, attributed |
| **Position Evolution** | Who shifted, who was rigid, what caused movement |
| **Surprising Insights** | What a casual observer would have missed |
| **Common Ground** | What the agents actually agreed on, even implicitly |
| **Unresolved Cruxes** | Specific empirical/ethical questions that remain open |
| **Final Recommendation** | A concrete, specific answer — not a hedge |
| **Confidence Score** | 0–100 with one-sentence justification |

### Scorecard

The report ends with a scorecard (the replay page shows it too, above the speeches), computed from the transcript with no
model involved, so it costs nothing and is the
same for every provider. It scores the debate, not the truth of the topic. Output of a 3-round `--dry-run` (the
canned speakers repeat their placeholder sentence, which the scorecard counts):

```text
| Agent | Stance by round | Shifts | Moved | Repeats |
|-------|-----------------|--------|-------|---------|
| The Analyst | for → for → for | 0 | no | 2 |
| The Pragmatist | against → against → for | 1 | yes (against → for) | 2 |
| The Devil's Advocate | for → for → for | 0 | no | 2 |

**Changed position:** The Pragmatist.

**Repeated arguments:** 6 sentence(s) restated a speaker's own earlier sentence (at least 80% the same words).
```

The stance comes from each turn's `POSITION:` line (`-` when it is missing; that round is not counted as a change of
mind). A repeat is a sentence of 8 or more words that shares at least 80% of its words with one of the same speaker's
earlier sentences.

---

## 📋 Presets

| Preset | Agents | Best For |
|--------|--------|----------|
| `neutral` | The Analyst, The Pragmatist, The Devil's Advocate | General-purpose balanced analysis |
| `debate_club` | The Optimist, The Pessimist, The Contrarian, The Pragmatist | Multi-perspective stress testing |
| `devils_advocate` | The Proponent, The Opponent | Quick, sharp pro/con on any topic |
| `investor_panel` | The VC, The Angel, The Sceptic | Startup & investment decisions |
| `investment_styles` | The Value Investor, The Macro Strategist, The Disruption Bull | Investment thesis analysis |
| `startup_team` | CEO, CTO, CFO | Business strategy & technical decisions |
| `tech_builders` | The Product Perfectionist, The Pragmatic Systems Engineer, The Frontier AI Builder | Technology strategy & product decisions |
| `philosophy` | Stoic, Utilitarian, Existentialist, Pragmatist | Ethics, values, life decisions |
| `ethics_panel` | Utilitarian, Kantian, Virtue Ethicist, Care Ethicist | Moral philosophy & applied ethics |
| `scientific_panel` | The Empiricist, The Theorist, The Sceptic, Translational Scientist | Science & research questions |
| `science_archetypes` | The Theorist, The Explainer, The Experimentalist | Scientific intuition & discovery |
| `medical_panel` | Clinician, Epidemiologist, Bioethicist, Health Economist | Healthcare & public health decisions |
| `legal_panel` | The Advocate, The Judge, The Legal Scholar, The Policy Analyst | Legal & regulatory questions |
| `statecraft` | The Crisis Leader, The Reconciler, The Consensus Builder | Geopolitics, policy & leadership |
| `product_design` | The User, The Designer, The Engineer, The PM | Product & UX decisions |
| `crypto_council` | The Maximalist, The DeFi Builder, The Sceptic | Crypto & blockchain evaluation |

```bash
# List all presets with participants
agora presets
```

---

## 🏛️ Formats

A preset only chooses the speakers. A **format** is a whole institution: fixed roles, a fixed sequence of phases,
rules every speaker gets, a disclaimer shown in the terminal and at the top of the report, and the shape of the final
output. It is a YAML file in `agora/formats/` (the spec is at the top of `agora/formats/__init__.py`).

| Format | Roles | Rounds | Final output |
|--------|-------|--------|--------------|
| `committee` | The Bull, The Bear, The Risk Officer, The Quant, The Devil's Advocate | 4 (opening, rebuttal, cross-examination, closing) | The chair's decision memo: thesis, strongest case for and counter, risks, **dissent kept by name**, what would change our minds, unverified claims, an assessment of how the thesis held up |
| `court` | The Prosecution, The Defence, The Expert Witness, The Juror | 4 (same phases) | The judge's judgment: the question and its elements, burden and standard of proof, findings per disputed issue, verdict, **minority opinion**, what would have changed the outcome, assumed facts and unverified law |
| `redteam` | The Plan Owner, The Red Team Lead, The Pre-Mortem Analyst, The Mitigation Engineer | 4 (same phases) | The red-team report: the plan and its assumptions, top risks ranked (stated fact or speculation), assumptions that did not hold, mitigations with cost and remaining risk, **what survived**, tripwires, unverified claims |

```bash
agora formats
agora run --format committee --topic "Is a broad index fund overvalued after a strong decade?"
agora run --format court --topic "Did the fictional baker breach the contract by delivering the wedding cake a day late?"
agora run --format redteam --topic "Should we keep all nightly backups in one cloud region?"
```

```text
Available formats:

  committee — Investment Committee (4 rounds)
    Bull, bear, risk officer, quant and devil's advocate test a thesis; the
chair writes a decision memo that keeps the dissent.
    The Bull, The Bear, The Risk Officer, The Quant, The Devil's Advocate

  court — Moot Court (4 rounds)
    Prosecution, defence, a neutral expert and a juror argue a case; the judge
writes a verdict that applies the burden of proof and keeps the minority
opinion.
    The Prosecution, The Defence, The Expert Witness, The Juror

  redteam — Red Team Review (4 rounds)
    A plan's owner defends it while a red team, a pre-mortem analyst and a
mitigation engineer try to break it; the report ranks the risks and says what
survived.
    The Plan Owner, The Red Team Lead, The Pre-Mortem Analyst, The Mitigation
Engineer
```

The committee is an educational exercise: every speaker is told never to recommend buying, selling, holding or
sizing a position, and the memo assesses the argument, not a trade. It is not investment advice. The court is a moot court
for learning how arguments meet a burden of proof: use fictional or historic public cases, never real ongoing cases or
private persons; agents are told to mark assumed facts and not to present laws they are unsure of as real. It is not
legal advice. The red-team review attacks a plan, product or decision before reality does: it critiques ideas, not
people, and stays at design level (agents are told never to write exploit code or attack instructions, or to aim at a
real system or person). `--format` cannot be combined with `--preset`, and the format fixes the number of rounds.

---

## Custom Personas

Create your own panel with a YAML file:

```yaml
# my_panel.yaml
name: "My Custom Panel"
agents:
  - name: "The Optimist"
    role: "You always see the bright side and focus on opportunities. You are rigorous about it — you back optimism with historical evidence of progress and specific mechanisms, not just positive thinking."
  - name: "The Realist"
    role: "You ground every discussion in data, constraints, and precedent. You challenge optimism when it outpaces evidence, and pessimism when it ignores real solutions."
  - name: "The Contrarian"
    role: "You challenge whatever position is emerging as consensus. You are not negative — you stress-test ideas by arguing the minority position to ensure no angle goes unexplored."
```

Then run it with `--agents` by name, or drop it in the `personas/` directory and use `--preset my_panel`.

---

## Advanced Usage

```bash
# More rounds for deeper analysis (5 is the default)
agora run --topic "Topic" --preset ethics_panel --rounds 7

# Dynamic termination: stop when consensus is reached, jump to closing
agora run --topic "Topic" --preset neutral --dynamic

# Adjust the convergence threshold (default: 0.75)
agora run --topic "Topic" --preset neutral --dynamic --convergence 0.65

# Disable moderator interventions between rounds
agora run --topic "Topic" --preset debate_club --no-interventions

# Disable streaming (show full responses after completion)
agora run --topic "Topic" --preset neutral --no-stream

# Use a specific model
agora run --topic "Topic" --preset startup_team --model opus
agora run --topic "Topic" --preset neutral --provider openai --model gpt4o-mini

# Save reports to a custom directory. Each run writes debate_<topic>_<time>.md and, with the same name,
# a .json transcript (rounds, phases, scores, moderator, synthesis; schema: docs/transcript.schema.json)

# Turn a transcript into one self-contained HTML page (positions per round, consensus, the scorecard,
# every speech, the synthesis; loads nothing from the network, so it can be shared as a file)
agora replay ./my_reports/debate_topic_20261119_155605.json            # writes the .html next to it
agora run --topic "Topic" --preset neutral --replay                    # or write it right after the debate
agora run --topic "Topic" --preset neutral --output ./my_reports

# Use custom agent names (each gets a generic analytical persona)
agora run --topic "Should we raise prices?" --agents "CFO,Head of Sales,Customer Success Lead"

# Generate a 4-agent neutral panel
agora run --topic "Topic" --agents 4
```

---

## Limitations

Agora is a small hobby project. Know what you are getting:

- **Tests cover the logic, not the models.** CI runs `pytest` on Linux and Windows (Python 3.9 and 3.13): phases, consensus scoring, presets, reports and the `run` command end to end through `--dry-run`. No test calls a real provider, so the provider code (API calls, retries, model IDs) is only checked by running debates by hand.
- **Install from source only.** It is not on PyPI. Presets are read from the repo's `personas/` folder, so use the editable install (`pip install -e .`) shown above.
- **Model aliases are pinned to 2025 model IDs** (for example `sonnet` → `claude-sonnet-4-20250514`, `flash` → `gemini-2.0-flash`). Providers retire models; if an alias fails, pass a current full model ID with `--model`. Gemini support uses the older `google-generativeai` SDK.
- **The scorecard reads words, not meaning.** A stance comes from simple word matching on the `POSITION:` line, and a repeat is word overlap, so a paraphrased argument is not caught. Steelman checks and unresolved cruxes are not scored yet.
- **The consensus meter is a rough heuristic.** It combines keyword overlap with simple word matching on each agent's `POSITION:` line. It does not understand meaning and can misread negations.
- **Every agent is the same underlying model** playing a role. Debates can converge because of that, not because an argument won.
- **Personas are archetypes, not real people.** The presets describe styles of thinking (for example the value investor or the crisis leader). They deliberately do not name or imitate real people, living or dead; before 2026-11-16 four presets did, and they were replaced for that reason. Your own presets should follow the same rule.
- **Not advice.** Output is generated text for thinking things through. It is not investment, financial, legal or medical advice. Check facts before acting on anything.
- **Cost.** A default 5-round debate with 3 agents makes roughly 20 model calls (turns, moderator checks, synthesis) and you pay for them on your own API key.

---

## 🔧 Troubleshooting

### `agora` command not found (Windows)

```bash
python -m agora run --topic "Your topic" --preset neutral
```

Or add Python's Scripts directory to your PATH:
```bash
python -c "import site; print(site.getusersitepackages().replace('site-packages','Scripts'))"
```

### Unicode/encoding errors (Windows)

```bash
# Command Prompt
set PYTHONIOENCODING=utf-8

# PowerShell
$env:PYTHONIOENCODING="utf-8"
```

### API key not found

Agora checks for the key matching your provider. Make sure the right variable is set:

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."

# Check which providers are ready
agora providers
```

### Python version errors

Agora requires Python 3.9+:
```bash
python --version
```

---

## Contributing

Contributions are welcome:

- 🐛 Report bugs via [GitHub Issues](https://github.com/bernhardbrugger/agora/issues)
- 💡 Suggest or submit new presets (drop a YAML in `personas/` and open a PR)
- 🔧 Submit pull requests — see [CONTRIBUTING.md](CONTRIBUTING.md)
- ⭐ Star the repo if it helped you think through a tough decision

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

*If this tool helped you think through a tough decision, consider starring the repo.*

</div>
