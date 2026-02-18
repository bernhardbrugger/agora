# agora

CLI framework for multi-agent debates powered by Claude.

Multiple AI agents with distinct personas debate a topic in rounds, then a neutral moderator synthesizes the key insights and delivers a recommendation.

## Installation

```bash
git clone https://github.com/yourusername/agora.git
cd agora
pip install -e .
```

## Setup

Set your Anthropic API key:

```bash
cp .env.example .env
# Edit .env and add your key
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Basic debate with named agents

```bash
agora run --agents "Skeptiker,Optimist,Pragmatiker" --topic "Soll ich fundraisen?" --rounds 3
```

### Quick debate with neutral agents

```bash
agora run --topic "Should we build a monolith or microservices?" --agents 3
```

### Use a preset persona panel

```bash
agora run --preset investor_panel --topic "My SaaS startup charges $50/mo and has 200 users"
agora run --preset philosophy --topic "Is it ethical to work at a company you disagree with?"
agora run --preset startup_team --topic "Should we pivot to B2B?"
```

### List available presets

```bash
agora presets
```

## Available Presets

| Preset | Agents | Best for |
|--------|--------|----------|
| `neutral` | Analyst, Pragmatist, Devil's Advocate | General-purpose balanced debate |
| `investor_panel` | VC, Angel, Skeptical Investor | Evaluating startup/fundraising decisions |
| `startup_team` | CEO, CTO, CFO | Internal strategy decisions |
| `philosophy` | Stoic, Utilitarian, Existentialist | Ethical and philosophical questions |
| `devils_advocate` | Proponent, Opponent | Pro/con analysis of any topic |

## How It Works

1. Each agent receives a system prompt defining their persona
2. Agents respond in rounds, each seeing the full debate history
3. After each round, a consensus meter shows how aligned/divided positions are
4. After all rounds, a neutral moderator synthesizes the debate into:
   - Key arguments FOR
   - Key arguments AGAINST
   - Surprising insights
   - Final recommendation with confidence score

## Output

Debates are automatically saved as Markdown reports in the `reports/` directory.

## Custom Personas

Create a YAML file in `personas/`:

```yaml
name: "My Custom Panel"
agents:
  - name: "Optimist"
    role: "You always see the bright side and argue for ambitious action..."
  - name: "Realist"
    role: "You ground discussions in data and historical precedent..."
```

Then use it:

```bash
agora run --preset my_custom_panel --topic "Your topic here"
```

## Models

- **Debate agents:** claude-opus-4-5 (high quality reasoning)
- **Moderator:** claude-opus-4-5 (synthesis quality)

## License

MIT
