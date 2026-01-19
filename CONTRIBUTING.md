# Contributing to AI Desktop Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## 🤝 How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/yourusername/ai-desktop-assistant/issues) first
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (Windows version, Python version, GPU)
   - Relevant logs from `logs/` directory

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would benefit users

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests
5. Run tests: `pytest`
6. Commit with semantic messages (see below)
7. Push and create a Pull Request

---

## 📝 Commit Message Format

Use semantic commit messages:

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvement |
| `security` | Security fix |

### Examples

```
feat(speech): add noise suppression to ASR
fix(avatar): correct lip sync timing
docs(readme): update installation instructions
test(core): add watchdog unit tests
```

---

## 🧪 Testing

### Running Tests

```powershell
# Activate environment
.\venv\Scripts\activate

# Run all tests
pytest

# Run specific test file
pytest tools/test_core_smoke.py

# Run with coverage
pytest --cov=core --cov-report=html
```

### Writing Tests

- Place tests in `tools/` directory
- Name test files as `test_*.py`
- Use pytest fixtures for common setup
- Mock external dependencies (LLM, audio devices)

---

## 🎨 Code Style

### Python Style Guide

- Follow PEP 8
- Maximum line length: 120 characters
- Use type hints where possible
- Document functions with docstrings

### Tools

```powershell
# Format code
black . --line-length 120

# Sort imports
isort .

# Lint
flake8 --max-line-length 120

# Type check
mypy core/ --ignore-missing-imports
```

### Pre-commit Hooks

The project uses pre-commit hooks. Install them:

```powershell
pip install pre-commit
pre-commit install
```

---

## 📁 Project Structure

When adding new features:

```
core/           → Main application logic
speech/         → Voice I/O (ASR, TTS)
brain/          → AI/LLM integration
avatar/         → Visual representation
automation/     → Desktop control
ui/             → User interface
tools/          → Utilities and tests
config/         → Configuration
```

---

## 🔀 Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add entry to CHANGELOG.md (under Unreleased)
4. Request review from maintainers
5. Address feedback
6. Squash commits if requested

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`, `isort`)
- [ ] No linting errors (`flake8`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow format

---

## 🏷️ Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature request |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `priority: high` | Urgent issues |
| `wontfix` | Will not be addressed |

---

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: [contact@example.com]

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Every contribution helps make this project better. Thank you for taking the time to contribute!
