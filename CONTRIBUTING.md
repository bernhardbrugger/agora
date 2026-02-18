# Contributing to Agora

Thanks for your interest in contributing! Here's how you can help.

## 🎭 Submit a Persona Preset

The easiest way to contribute! Create a YAML file in `personas/`:

```yaml
name: "Your Panel Name"
agents:
  - name: "Agent Name"
    role: "Detailed persona description..."
  - name: "Another Agent"
    role: "Their perspective and argumentative style..."
```

**Guidelines for good presets:**
- 2-5 agents per panel
- Distinct, non-overlapping perspectives
- Detailed role descriptions (at least 2 sentences)
- Clear use case (when would someone use this panel?)

## 🐛 Report Bugs

Open an issue with:
- What you expected
- What actually happened
- Steps to reproduce
- Python version and OS

## 🚀 Submit Features

1. Open an issue describing the feature
2. Fork the repo
3. Create a branch (`git checkout -b feature/your-feature`)
4. Make your changes
5. Submit a PR

## 📝 Code Style

- Type hints everywhere
- Docstrings on all public methods
- Keep it simple — this is a CLI tool, not a framework

## 🧪 Testing

```bash
python -m pytest tests/
```
