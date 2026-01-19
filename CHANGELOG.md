# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-01-19

### 🎉 Initial Release

First public release of the AI Desktop Assistant.

### Added

#### Core Features
- **Voice Control**: Push-to-talk and toggle mode with Faster-Whisper STT
- **Local TTS**: Piper neural text-to-speech with multiple voices
- **Avatar System**: Live2D animated avatar with emotion and lip-sync
- **Desktop Automation**: Keyboard, mouse, and application control
- **Local LLM**: Ollama integration with Mistral, LLaMA, CodeLlama

#### Self-Healing System
- **Watchdog Monitor**: Automatic health checking and component monitoring
- **Repair Engine**: Library of safe, idempotent repair actions
- **Git-Backed Operations**: All changes committed with rollback capability
- **Circuit Breaker**: Prevents runaway repair loops (3 attempts/10 min)

#### Git Power Upgrades
- **Git Bisect**: Automatic bug hunting in O(log n) time
- **Diff Validation**: Abort if unexpected files modified
- **Semantic Commits**: Machine-readable commit format
- **Static Analysis**: flake8, mypy, bandit integration
- **Failure Tagging**: git tag failed-fix-<hash> for learning

#### Safety Features
- **Kill Switch**: Ctrl+Alt+K immediately stops all operations
- **Confirmation Dialogs**: High-risk actions require approval
- **Audit Logging**: Full history of all actions
- **Privacy First**: 100% local processing, no cloud required

### Configuration
- Environment-based configuration via `.env`
- Device selection for microphone (MIC_DEVICE_INDEX)
- Configurable model sizes for STT and LLM
- Adjustable autonomy levels

### Documentation
- README.md with quick start guide
- INSTALL.md with detailed setup instructions
- ARCHITECTURE.md with system overview
- SAFETY.md with kill switch documentation
- PRIVACY.md with data handling policies

---

## [Unreleased]

### Planned Features
- Wake word detection ("Hey Assistant")
- Continuous background listening mode
- Multi-language support
- Plugin system for custom actions
- Web dashboard for configuration
- Mobile companion app

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2026-01-19 | Initial release |

---

## Migration Notes

### From Pre-Release Versions

If upgrading from a development version:

1. Backup your `.env` file
2. Pull latest changes: `git pull origin main`
3. Install new dependencies: `pip install -r requirements.txt`
4. Compare `.env.example` with your `.env` for new settings
5. Run tests: `pytest tools/test_core_smoke.py`

---

## Contributors

- Primary Developer: [Your Name]
- See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute

---

## Links

- [GitHub Repository](https://github.com/yourusername/ai-desktop-assistant)
- [Issue Tracker](https://github.com/yourusername/ai-desktop-assistant/issues)
- [Documentation](https://github.com/yourusername/ai-desktop-assistant/wiki)
