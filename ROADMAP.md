# 🗺️ Roadmap

This document outlines the planned development of AI Desktop Assistant.

## 📍 Current Version: v1.0.1

Released: January 2026

### ✅ Completed Features
- [x] Voice recognition (Whisper + faster-whisper)
- [x] Local TTS (pyttsx3 / Windows SAPI)
- [x] Push-to-talk with configurable hotkeys
- [x] Ollama LLM integration
- [x] Self-healing watchdog system
- [x] Git-backed autonomous repair
- [x] Circuit breaker for repair loops
- [x] VTube Studio avatar integration
- [x] Desktop automation basics
- [x] Kill switch (Ctrl+Alt+K)

---

## 🎯 Version 1.1 (Q2 2026)

**Theme: Stability & Cross-Platform**

### High Priority
- [ ] **Linux support** (Ubuntu 22.04+, Debian 12+)
  - systemd service file
  - PulseAudio/PipeWire audio support
  - .deb package
- [ ] **Improved error messages** — Human-readable errors with fix suggestions
- [ ] **Plugin system** — Load custom tools from `plugins/` directory
- [ ] **Better noise cancellation** — RNNoise integration

### Medium Priority
- [ ] **Configuration wizard** — First-run setup GUI
- [ ] **Model auto-download** — Automatically pull Whisper models
- [ ] **Hotkey customization UI** — Visual hotkey editor
- [ ] **Log viewer** — Built-in log browser

### Low Priority
- [ ] **Docker support** — Containerized deployment
- [ ] **ARM64 support** — Raspberry Pi 4/5

---

## 🎯 Version 1.2 (Q3 2026)

**Theme: Intelligence & Extensibility**

### High Priority
- [ ] **macOS support** — Native macOS build
- [ ] **Multi-language STT** — Support for 10+ languages
- [ ] **Custom wake words** — "Hey Assistant" trigger
- [ ] **Web UI dashboard** — Browser-based control panel

### Medium Priority
- [ ] **Conversation memory** — Long-term context storage
- [ ] **Task scheduling** — "Remind me at 3pm"
- [ ] **Clipboard integration** — Read/write clipboard
- [ ] **Screenshot OCR** — Read text from screen

### Low Priority
- [ ] **Voice cloning** — Custom TTS voices
- [ ] **Multi-monitor support** — Screen selection

---

## 🎯 Version 2.0 (Q4 2026)

**Theme: Ecosystem & Integration**

### Vision
- [ ] **Mobile companion app** — Android/iOS remote control
- [ ] **Smart home integration** — Home Assistant, MQTT
- [ ] **Calendar integration** — Local calendar sync
- [ ] **Email integration** — Local email client
- [ ] **Code completion** — VS Code extension
- [ ] **Meeting assistant** — Transcribe & summarize meetings

---

## 🤝 Community Requests

We track community-requested features here. Vote with 👍 on issues!

| Request | Votes | Status |
|---------|-------|--------|
| Linux support | ⭐⭐⭐ | Planned v1.1 |
| Multi-language | ⭐⭐ | Planned v1.2 |
| Wake word | ⭐⭐ | Planned v1.2 |
| Mobile app | ⭐ | Planned v2.0 |

---

## 📝 How to Request Features

1. Check [existing issues](https://github.com/rupac4530-creator/ai-desktop-assistant/issues)
2. Open a [feature request](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=feature_request.md)
3. Describe the feature and use case
4. Vote on existing requests with 👍

---

## 🏗️ Architecture Decisions

Major technical decisions are documented here:

| Decision | Rationale |
|----------|-----------|
| Offline-first | Privacy, reliability, speed |
| Ollama for LLM | Local, open-source, multi-model |
| faster-whisper | 4x faster than OpenAI Whisper |
| Git for repair | Auditable, reversible changes |
| Python | Rapid development, ML ecosystem |

---

## 📅 Release Schedule

| Version | Target Date | Status |
|---------|-------------|--------|
| v1.0.1 | Jan 2026 | ✅ Released |
| v1.1.0 | Apr 2026 | 🔄 In Progress |
| v1.2.0 | Jul 2026 | 📋 Planned |
| v2.0.0 | Oct 2026 | 💭 Vision |

---

*This roadmap is subject to change based on community feedback and contributor availability.*

**Want to help?** Check out [good first issues](https://github.com/rupac4530-creator/ai-desktop-assistant/labels/good%20first%20issue)!
