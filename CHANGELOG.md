# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive documentation (ROADMAP, SECURITY, CODE_OF_CONDUCT, FAQ)
- GitHub issue and PR templates
- Contributors guide and SUPPORT.md
- docs/onepager.html for recruiters

### Changed
- README.md rewritten for professional open-source style

---

## [1.0.1] - 2025-06-24

### Fixed
- **cuBLAS DLL not found** — Added NVIDIA library path resolution at module load in `speech/asr.py`
- **TTS health check false positives** — Fixed watchdog to check `_engine` attribute for LocalTTS
- **Microphone "No audio frames"** — Locked to Intel Microphone Array (device index 1)

### Added
- Professional documentation suite (INSTALL.md, SAFETY.md, PRIVACY.md, ARCHITECTURE.md)
- `.env.example` for easy configuration
- MIT License
- Outreach templates (LinkedIn post, recruiter email)

### Changed
- Improved error messages for CUDA initialization
- Better device selection logging

---

## [1.0.0] - 2025-06-20

### 🎉 Initial Release

First public release of the AI Desktop Assistant.

### Added

#### Core Features
- **Voice Control**: Push-to-talk and toggle mode with Faster-Whisper STT
- **Local TTS**: pyttsx3 text-to-speech (SAPI5 on Windows)
- **Desktop Automation**: Keyboard, mouse, and application control
- **Local LLM**: Ollama integration with Mistral, LLaMA, Phi-3

#### Self-Healing System
- **Watchdog Monitor**: Automatic health checking and component monitoring
- **Repair Engine**: Library of safe, idempotent repair actions
- **Git-Backed Operations**: All changes committed with rollback capability
- **Circuit Breaker**: Prevents runaway repair loops (3 attempts/10 min)

#### Safety Features
- **Kill Switch**: Ctrl+Alt+K immediately stops all operations
- **Confirmation Dialogs**: High-risk actions require approval
- **Audit Logging**: Full history of all actions
- **Privacy First**: 100% local processing, no cloud required

### Configuration
- Environment-based configuration via `.env`
- Device selection for microphone (MIC_DEVICE_INDEX)
- Configurable model sizes for STT and LLM
- CUDA acceleration support

### Documentation
- README.md with quick start guide
- INSTALL.md with detailed setup instructions
- ARCHITECTURE.md with system overview
- SAFETY.md with kill switch documentation
- PRIVACY.md with data handling policies

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.1 | 2025-06-24 | cuBLAS fix, TTS fix, pro documentation |
| 1.0.0 | 2025-06-20 | Initial release |

---

## Migration Notes

### Upgrading to 1.0.1

1. Install new CUDA dependencies:
   ```bash
   pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
   ```

2. Copy `.env.example` to `.env` and configure

3. Verify microphone device index:
   ```bash
   python -c "import sounddevice; print(sounddevice.query_devices())"
   ```

### From Pre-Release Versions

If upgrading from a development version:

1. Backup your `.env` file
2. Pull latest changes: `git pull origin main`
3. Install dependencies: `pip install -r requirements.txt`
4. Compare `.env.example` with your `.env`
5. Run tests: `pytest tools/test_core_smoke.py`

---

## Contributors

- **Bedanta Chatterjee** — Creator & Maintainer
- See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute

---

## Links

- [GitHub Repository](https://github.com/rupac4530-creator/ai-desktop-assistant)
- [Issue Tracker](https://github.com/rupac4530-creator/ai-desktop-assistant/issues)
- [Roadmap](ROADMAP.md)

---

[Unreleased]: https://github.com/rupac4530-creator/ai-desktop-assistant/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/rupac4530-creator/ai-desktop-assistant/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rupac4530-creator/ai-desktop-assistant/releases/tag/v1.0.0
