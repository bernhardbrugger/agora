<div align="center">

# 🏛️ Agora

### *Where AI minds debate so you don't have to*

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI](https://img.shields.io/badge/Powered%20by-OpenAI-412991.svg)](https://openai.com)

**Agora** is a CLI tool that creates multi-agent AI debates on any topic. Pick a preset panel of experts — from startup founders to philosophers to world leaders — and watch them argue, agree, and synthesize insights in real time.

[Features](#features) · [Installation](#installation) · [Quick Start](#-quick-start) · [Presets](#-presets) · [Troubleshooting](#-troubleshooting)

</div>

---

## Features

- 🎭 **12 Built-in Presets** — From investor panels to philosophy roundtables to crypto councils
- 🔧 **Custom Personas** — Define your own debaters with simple YAML
- 🌊 **Real-time Streaming** — Watch the debate unfold live in your terminal
- 🔄 **Multi-round Debates** — Agents respond to each other, not just the topic
- 📊 **Automatic Synthesis** — Get a balanced summary after the debate
- 🤖 **Any OpenAI Model** — Use GPT-4o, GPT-4o-mini, o1, or any compatible model

---

## 🤖 Supported Providers

Use any major LLM provider — just set your API key and go:

| Provider | Flag | Models | API Key |
|----------|------|--------|---------|
| **Anthropic** (default) | `--provider anthropic` | `haiku`, `sonnet`*, `opus` | `ANTHROPIC_API_KEY` |
| **OpenAI** | `--provider openai` | `gpt4o`*, `gpt4o-mini`, `o1`, `o3-mini` | `OPENAI_API_KEY` |
| **Google Gemini** | `--provider gemini` | `flash`*, `pro`, `thinking` | `GOOGLE_API_KEY` |
| **xAI Grok** | `--provider grok` | `grok`*, `grok-mini` | `XAI_API_KEY` |

*\* = default model for that provider*

```bash
# Use Claude (default)
agora run --topic "Your topic" --preset neutral

# Use GPT-4o
agora run --topic "Your topic" --preset neutral --provider openai

# Use Gemini Flash (cheapest)
agora run --topic "Your topic" --preset neutral --provider gemini --model flash

# Use Grok
agora run --topic "Your topic" --preset neutral --provider grok

# List providers and check which API keys are configured
agora providers
```

Install optional provider dependencies:
```bash
pip install agora-debate[openai]   # For OpenAI/Grok
pip install agora-debate[gemini]   # For Google Gemini
pip install agora-debate[all]      # Everything
```


## Installation

### macOS / Linux

```bash
# Clone the repository
git clone https://github.com/bernhardbrugger/agora.git
cd agora

# Install in development mode
pip install -e .

# Verify installation
agora --help
```

### Windows

```bash
# Clone and install
git clone https://github.com/bernhardbrugger/agora.git
cd agora
pip install -e .

# If 'agora' command is not found, use:
python -m agora.cli run --topic "Your topic" --preset neutral
```

> **💡 Windows Tip:** If the `agora` command isn't recognized, it's likely a PATH issue. Python scripts are installed to a directory that may not be in your PATH. Using `python -m agora.cli` always works as a reliable alternative.

### Requirements

- Python 3.9 or higher
- An OpenAI API key

---

## Setup

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# On Windows (Command Prompt):
set OPENAI_API_KEY=sk-your-key-here

# On Windows (PowerShell):
$env:OPENAI_API_KEY="sk-your-key-here"
```

---

## 🚀 Quick Start

```bash
# Classic balanced debate
agora run --topic "Should we colonize Mars?" --preset neutral

# Get investment advice from legendary investors
agora run --topic "Is NVIDIA overvalued at current prices?" --preset investment_legends

# Debate AI ethics with philosophers
agora run --topic "Should AI have rights?" --preset philosophy

# Get startup feedback from a virtual board
agora run --topic "We're pivoting from B2C to B2B SaaS" --preset startup_team

# Ask science's greatest minds
agora run --topic "Is consciousness computable?" --preset science_minds

# Geopolitical analysis from world leaders
agora run --topic "How should NATO respond to Arctic territorial claims?" --preset world_leaders

# Product design review
agora run --topic "Should we add social features to our finance app?" --preset product_design

# Crypto investment thesis
agora run --topic "Is Ethereum a good long-term hold?" --preset crypto_council

# Tech strategy from Silicon Valley legends
agora run --topic "Should our startup go open-source?" --preset tech_legends

# Quick pro/con analysis
agora run --topic "Should I quit my job to start a company?" --preset devils_advocate
```

---

## 📋 Presets

| Preset | Agents | Best For |
|--------|--------|----------|
| `neutral` | Analyst, Pragmatist, Devil's Advocate | General-purpose balanced analysis |
| `investor_panel` | VC, Angel, Skeptical Investor | Startup & investment decisions |
| `startup_team` | CEO, CTO, CFO | Business strategy & technical decisions |
| `philosophy` | Stoic, Utilitarian, Existentialist | Ethics, life decisions, values |
| `devils_advocate` | Proponent, Opponent | Quick pro/con on any topic |
| `tech_legends` | Jobs, Torvalds, Altman | Technology strategy & product decisions |
| `investment_legends` | Buffett, Dalio, Wood | Investment thesis analysis |
| `debate_club` | Optimist, Pessimist, Contrarian, Pragmatist | Thorough multi-perspective analysis |
| `science_minds` | Einstein, Feynman, Curie | Scientific & research questions |
| `world_leaders` | Churchill, Mandela, Merkel | Geopolitics, policy & leadership |
| `product_design` | User, Designer, Engineer, PM | Product & UX decisions |
| `crypto_council` | Maximalist, DeFi Builder, Skeptic | Crypto & blockchain evaluation |

---

## Custom Personas

Create your own debate panel with a simple YAML file:

```yaml
# my_panel.yaml
name: "My Custom Panel"
agents:
  - name: "The Optimist"
    role: "You always see the bright side and focus on opportunities."
  - name: "The Realist"
    role: "You ground discussions in data and practical constraints."
  - name: "The Visionary"
    role: "You think 10 years ahead and challenge conventional wisdom."
```

```bash
agora run --topic "Your topic" --persona my_panel.yaml
```

---

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent 1    │     │   Agent 2    │     │   Agent 3    │
│  (e.g. VC)   │     │ (e.g. Angel) │     │(e.g. Skeptic)│
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                    Debate Rounds                         │
│  Each agent sees the full conversation history and       │
│  responds in character, building on others' arguments    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Synthesis Agent                         │
│  Summarizes key points, areas of agreement/disagreement  │
│  and provides a balanced conclusion                      │
└─────────────────────────────────────────────────────────┘
```

---

## Sample Output

```
$ agora run --topic "Should startups use AI for hiring?" --preset startup_team

🏛️ Agora — Starting debate: Should startups use AI for hiring?
Using preset: startup_team (CEO, CTO, CFO)
Rounds: 2 | Model: gpt-4o

━━━ Round 1 ━━━

💬 CEO:
AI-assisted hiring could be a massive competitive advantage for us...

💬 CTO:
From a technical standpoint, we need to be careful about bias in training data...

💬 CFO:
Let's look at the numbers. Our current cost-per-hire is...

━━━ Synthesis ━━━

📊 The panel agrees that AI can streamline hiring but diverges on implementation...
```

---

## Advanced Usage

```bash
# Choose a specific model
agora run --topic "Topic" --preset neutral --model gpt-4o-mini

# Disable streaming (get full response at once)
agora run --topic "Topic" --preset neutral --no-stream

# More debate rounds for deeper discussion
agora run --topic "Topic" --preset neutral --rounds 3

# Combine options
agora run --topic "Is remote work better?" --preset startup_team --model gpt-4o --rounds 3
```

---

## 🔧 Troubleshooting

### `agora` command not found (Windows)

Python installs scripts to a directory that may not be in your system PATH. Use this instead:

```bash
python -m agora.cli run --topic "Your topic" --preset neutral
```

Or add Python's Scripts directory to your PATH:
- Find it with: `python -c "import site; print(site.getusersitepackages().replace('site-packages','Scripts'))"`
- Add that directory to your system PATH

### Unicode/encoding errors (Windows)

If you see encoding errors, set UTF-8 mode:

```bash
# Command Prompt
set PYTHONIOENCODING=utf-8

# PowerShell
$env:PYTHONIOENCODING="utf-8"
```

### `OPENAI_API_KEY` not set

Make sure you've exported your API key in the current terminal session:

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"
```

### Python version errors

Agora requires Python 3.9+. Check your version:

```bash
python --version
# or
python3 --version
```

---

## Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest new presets
- 🔧 Submit pull requests
- ⭐ Star the repo if you find it useful!

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ and too many API calls**

*If this tool helped you think through a tough decision, consider starring the repo!*

</div>
