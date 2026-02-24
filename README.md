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

- 🎭 **16 Built-in Presets** — From investment legends to ethics panels to medical boards
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

Install optional provider dependencies:
```bash
pip install agora-debate[openai]   # For OpenAI / Grok
pip install agora-debate[gemini]   # For Google Gemini
pip install agora-debate[all]      # Everything
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

```bash
# Classic balanced debate — 5 structured rounds
agora run --topic "Should we colonize Mars?" --preset neutral

# Investment thesis from legendary investors
agora run --topic "Is NVIDIA overvalued at current prices?" --preset investment_legends

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

# Tech legends on product strategy
agora run --topic "Should our startup go open-source?" --preset tech_legends

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

---

## 📋 Presets

| Preset | Agents | Best For |
|--------|--------|----------|
| `neutral` | The Analyst, The Pragmatist, The Devil's Advocate | General-purpose balanced analysis |
| `debate_club` | The Optimist, The Pessimist, The Contrarian, The Pragmatist | Multi-perspective stress testing |
| `devils_advocate` | The Proponent, The Opponent | Quick, sharp pro/con on any topic |
| `investor_panel` | The VC, The Angel, The Sceptic | Startup & investment decisions |
| `investment_legends` | Buffett, Dalio, Wood | Investment thesis analysis |
| `startup_team` | CEO, CTO, CFO | Business strategy & technical decisions |
| `tech_legends` | Jobs, Torvalds, Altman | Technology strategy & product decisions |
| `philosophy` | Stoic, Utilitarian, Existentialist, Pragmatist | Ethics, values, life decisions |
| `ethics_panel` | Utilitarian, Kantian, Virtue Ethicist, Care Ethicist | Moral philosophy & applied ethics |
| `scientific_panel` | The Empiricist, The Theorist, The Sceptic, Translational Scientist | Science & research questions |
| `science_minds` | Einstein, Feynman, Curie | Scientific intuition & discovery |
| `medical_panel` | Clinician, Epidemiologist, Bioethicist, Health Economist | Healthcare & public health decisions |
| `legal_panel` | The Advocate, The Judge, The Legal Scholar, The Policy Analyst | Legal & regulatory questions |
| `world_leaders` | Churchill, Mandela, Merkel | Geopolitics, policy & leadership |
| `product_design` | The User, The Designer, The Engineer, The PM | Product & UX decisions |
| `crypto_council` | The Maximalist, The DeFi Builder, The Sceptic | Crypto & blockchain evaluation |

```bash
# List all presets with participants
agora presets
```

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

# Save reports to a custom directory
agora run --topic "Topic" --preset neutral --output ./my_reports

# Use custom agent names (each gets a generic analytical persona)
agora run --topic "Should we raise prices?" --agents "CFO,Head of Sales,Customer Success Lead"

# Generate a 4-agent neutral panel
agora run --topic "Topic" --agents 4
```

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
