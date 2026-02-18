<div align="center">

# 🏛️ Agora

### Multi-Agent AI Debates in Your Terminal

*What if you could have Buffett, Thiel, and Soros debate your investment thesis?*
*Or let Stoic, Utilitarian, and Existentialist philosophers argue about your life choices?*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Agora** is a CLI framework where multiple AI agents with distinct personas debate any topic in structured rounds. A neutral moderator then synthesizes the key insights and delivers a recommendation with a confidence score.

[Installation](#installation) • [Quick Start](#quick-start) • [Presets](#presets) • [Custom Personas](#custom-personas) • [How It Works](#how-it-works)

</div>

---

## ✨ Features

- 🎭 **Distinct Personas** — Each agent has a unique personality, expertise, and argumentative style
- 🔄 **Multi-Round Debates** — Agents respond to each other, building and challenging arguments over rounds
- 📊 **Consensus Meter** — Visual indicator of how aligned or divided the agents are after each round
- 🏛️ **AI Moderator** — Neutral moderator synthesizes the debate: key arguments, surprising insights, final recommendation
- 🎨 **Beautiful Terminal UI** — Rich-powered colorful panels, progress indicators, and formatted output
- ⚡ **Streaming Responses** — Watch agents think in real-time (no more staring at a blank screen)
- 💰 **Cost Control** — Choose your model: `--model haiku` for cheap experiments, `sonnet` for daily use, `opus` for important decisions
- 📝 **Auto-saved Reports** — Every debate saved as a Markdown report in `reports/`
- 🧩 **Preset Panels** — Ready-made expert panels for common decision types
- 🛠️ **Custom Personas** — Create your own debate panels with simple YAML files

## 🚀 Installation

```bash
pip install agora-debate
```

Or from source:

```bash
git clone https://github.com/bernhardbrugger/agora.git
cd agora
pip install -e .
```

## ⚙️ Setup

```bash
export ANTHROPIC_API_KEY=your-key-here
```

Or create a `.env` file:

```bash
cp .env.example .env
# Add your Anthropic API key
```

## 🎯 Quick Start

### Run a debate with named agents

```bash
agora run --topic "Should I quit my job to start a startup?" --agents "Optimist,Realist,Pessimist"
```

### Use a preset expert panel

```bash
agora run --preset investor_panel --topic "My SaaS has 200 users at $50/mo. Should I raise a seed round?"
```

### Quick 2-agent pro/con analysis

```bash
agora run --preset devils_advocate --topic "Is Bitcoin a good long-term investment?"
```

### Philosophy mode 🧠

```bash
agora run --preset philosophy --topic "Is it ethical to work at a company you disagree with?"
```

### Budget-friendly debates

```bash
agora run --topic "Your topic" --agents 3 --model haiku    # ~$0.01 per debate
agora run --topic "Your topic" --agents 3 --model sonnet   # ~$0.10 per debate (default)
agora run --topic "Your topic" --agents 3 --model opus     # ~$1.00 per debate (highest quality)
```

## 🎭 Presets

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

```bash
agora presets  # List all available presets
```

## 🛠️ Custom Personas

Create a YAML file in `personas/`:

```yaml
name: "My Expert Panel"
agents:
  - name: "The Optimizer"
    role: "You are obsessed with efficiency and optimization. Every decision should maximize output per unit of input."
  - name: "The Visionary"
    role: "You think in 10-year horizons. Short-term pain is irrelevant if the long-term trajectory is right."
  - name: "The Skeptic"
    role: "You've seen it all before. You demand extraordinary evidence for extraordinary claims."
```

```bash
agora run --preset my_expert_panel --topic "Your topic"
```

## 🔧 How It Works

```
┌─────────────────────────────────────────┐
│             AGORA DEBATE ENGINE          │
├─────────────────────────────────────────┤
│                                         │
│  1. Topic + Persona Assignment          │
│     ↓                                   │
│  2. Round 1: Each agent speaks          │
│     ↓                                   │
│  3. Consensus Meter calculated          │
│     ↓                                   │
│  4. Round 2-N: Agents respond to each   │
│     other, challenge, build arguments   │
│     ↓                                   │
│  5. Moderator reads full transcript     │
│     ↓                                   │
│  6. Synthesis: Key arguments FOR/AGAINST│
│     Surprising insights                 │
│     Final recommendation + confidence   │
│     ↓                                   │
│  7. Report saved as Markdown            │
│                                         │
└─────────────────────────────────────────┘
```

## 📊 Sample Output

```
━━━━━━━━━━━━━━ AGORA — Multi-Agent Debate ━━━━━━━━━━━━━━

  Topic:  Should we pivot from B2C to B2B?
  Agents: CEO, CTO, CFO
  Rounds: 3

━━━━━━━━━━━━━━━ Round 1 of 3 ━━━━━━━━━━━━━━━

┌─── CEO ──────────────────────────────────────────┐
│ The B2B pivot makes strategic sense. Our B2C     │
│ CAC is $85 and climbing, while B2B prospects     │
│ are asking for exactly what we've built...       │
└──────────────────────────────────────────────────┘

┌─── CTO ──────────────────────────────────────────┐
│ Technically, we'd need 3-4 months of work:       │
│ multi-tenancy, RBAC, audit logs, SSO...          │
│ But the architecture supports it.                │
└──────────────────────────────────────────────────┘

┌─── CFO ──────────────────────────────────────────┐
│ The numbers tell a clear story: B2C LTV is       │
│ $240 vs B2B enterprise contracts averaging       │
│ $18K annually. But the sales cycle concern...    │
└──────────────────────────────────────────────────┘

  Consensus Meter (Round 1):
  ████████████████████████░░░░░░░░░░ 68% — Approaching Consensus
```

## 🤝 Contributing

Contributions are welcome! Especially:

- 🎭 **New persona presets** — Submit interesting expert panels
- 🌍 **Translations** — Help make Agora work in more languages
- 🧪 **Features** — Streaming, web UI, export formats

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT — use it, fork it, build on it.

---

<div align="center">

**Built by [Bernhard Brugger](https://github.com/bernhardbrugger)** 🏛️

*If Agora helped you make a better decision, give it a ⭐*

</div>
