#  AI Desktop Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CUDA](https://img.shields.io/badge/CUDA-Enabled-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Open Source](https://img.shields.io/badge/Open%20Source--red.svg)](#-philosophy)

**A fully autonomous, voice-controlled AI desktop assistant with self-healing capabilities, powered by local LLMs.**

>  **100% Local & Private** — All processing happens on your machine. No cloud required.

![Demo Screenshot](assets/demo_screenshot.png)

---

##  Why This Project?

This project was born from a simple idea: **AI assistants should work for you, not spy on you.**

- **Offline-first**: Works without internet after initial setup
- **Self-healing**: Automatically fixes its own bugs using Git-backed repair
- **Extensible**: Modular architecture — add your own tools, voices, or LLMs
- **Transparent**: Every action is logged, every change is reversible

---

##  Key Features

###  Voice Interface
- **Real-time speech recognition** via Whisper (GPU-accelerated)
- **Natural text-to-speech** with local voices
- Push-to-talk with configurable hotkeys
- Silence detection and voice activity detection

###  AI Brain (Local LLM)
- **Ollama integration** — runs Mistral, LLaMA, CodeLlama locally
- Zero cloud dependencies for core functionality
- Context-aware conversation memory
- Specialized models for coding tasks

###  Full Autonomy
- **Self-healing system** — detects and repairs its own errors
- Git-backed operations with automatic rollback
- Semantic commit messages for all changes
- Circuit breaker prevents runaway repair loops

###  System Control
- Open applications and websites
- Execute shell commands
- File and folder operations
- Screen reading and automation

###  Live2D Avatar
- VTube Studio integration via OSC
- Lip-sync with audio output
- Emotion-driven animations

---

##  Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/rupac4530-creator/ai-desktop-assistant.git
cd ai-desktop-assistant

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your settings

# 5. Install Ollama and pull a model
ollama pull mistral:7b-instruct

# 6. Run the assistant
python core\main_controller.py --tray
```

 **See [INSTALL.md](INSTALL.md) for detailed installation instructions.**

---

##  Hotkeys

| Key | Action |
|-----|--------|
| `Ctrl+Alt+Space` | Start recording (push-to-talk) |
| `Enter` | Stop recording |
| `Ctrl+Alt+T` | Toggle listening mode |
| `Ctrl+Alt+K` | **Kill switch** (emergency stop) |
| `Ctrl+Alt+A` | Toggle avatar visibility |

---

##  Safety First

This assistant has **full system access**. Safety measures include:

- **Kill switch** (`Ctrl+Alt+K`) — instantly stops all operations
- **Circuit breaker** — prevents infinite repair loops (3 attempts/10 min)
- **Git rollback** — all changes can be reverted
- **Disable autonomy** — run `disable_autopilot.bat` for safe mode

 **Read [SAFETY.md](SAFETY.md) before enabling full autonomy.**

---

##  Privacy

-  All speech processing happens **locally**
-  LLM runs on **your hardware** via Ollama
-  No telemetry or analytics
-  Voice recordings stored locally and auto-deleted
-  No cloud APIs required for core features

 **See [PRIVACY.md](PRIVACY.md) for complete data handling policies.**

---

##  Roadmap

We're building this in the open. Here's what's planned:

###  Version 1.1 (Next)
- [ ] Linux support (Ubuntu/Debian)
- [ ] Improved noise cancellation
- [ ] Plugin system for custom tools
- [ ] Better error messages

###  Version 1.2
- [ ] macOS support
- [ ] Multi-language voice recognition
- [ ] Custom wake words
- [ ] Web UI dashboard

###  Future Ideas
- [ ] Mobile companion app
- [ ] Smart home integration
- [ ] Calendar/email integration (local)
- [ ] Code completion assistance

**Have an idea?** [Open a feature request](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=feature_request.md)!

---

##  Contributing

**This is a community project. All contributions are welcome!**

Whether you're fixing a typo, adding a feature, or improving documentation — every contribution helps.

### Quick Links
-  [Contributing Guide](CONTRIBUTING.md)
-  [Report a Bug](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=bug_report.md)
-  [Request a Feature](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=feature_request.md)
-  [Good First Issues](https://github.com/rupac4530-creator/ai-desktop-assistant/labels/good%20first%20issue)

### How to Contribute

```bash
# 1. Fork the repo
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-desktop-assistant.git

# 3. Create a branch
git checkout -b feature/amazing-feature

# 4. Make changes and commit
git commit -m "feat: add amazing feature"

# 5. Push and open a PR
git push origin feature/amazing-feature
```

---

##  Philosophy

This project follows these principles:

1. **Privacy by Default** — Your data stays on your machine
2. **Offline First** — Core features work without internet
3. **Transparent AI** — Every action is logged and reversible
4. **Community Driven** — Built by users, for users
5. **Beginner Friendly** — Good documentation, clear code

We believe AI should **empower** users, not exploit them.

---

##  Project Structure

```
ai_desktop_assistant/
 core/                # Core engine and state
    main_controller.py
    repair_engine.py # Self-healing system
    watchdog.py      # Health monitoring
 speech/              # Voice I/O
    asr.py           # Speech-to-text
    local_tts.py     # Text-to-speech
 brain/               # AI/LLM integration
 automation/          # Desktop control
 tools/               # Utilities and tests
 logs/                # Runtime logs
```

 **See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.**

---

##  Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | Step-by-step installation guide |
| [SAFETY.md](SAFETY.md) | Kill switch and safety features |
| [PRIVACY.md](PRIVACY.md) | Data handling and privacy policy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and data flow |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

##  Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.10 | 3.11+ |
| **RAM** | 8 GB | 16+ GB |
| **GPU** | 4 GB VRAM | 6+ GB VRAM (NVIDIA) |
| **Storage** | 10 GB | 20+ GB (for models) |

---

##  License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

You are free to use, modify, and distribute this software.

---

##  Acknowledgments

- [Whisper](https://github.com/openai/whisper) — Speech recognition
- [Ollama](https://ollama.ai/) — Local LLM runtime
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) — Optimized Whisper
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) — Text-to-speech

---

##  Author

**Bedanta Chatterjee**
- GitHub: [@rupac4530-creator](https://github.com/rupac4530-creator)
- Email: rupac4530@gmail.com

---

<p align="center">
  <b>Built with  for privacy, autonomy, and open source</b>
  <br><br>
   <b>Star this repo if you find it useful!</b> 
</p>
