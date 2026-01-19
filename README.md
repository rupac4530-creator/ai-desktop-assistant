#  AI Desktop Assistant

[![Release v1.0.1](https://img.shields.io/badge/Release-v1.0.1-blue.svg)](https://github.com/rupac4530-creator/ai-desktop-assistant/releases/tag/v1.0.1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-Enabled-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Voice-controlled AI assistant that runs 100% locally. No cloud. No data leaves your machine.**

>  Privacy-first   Self-healing   GPU-accelerated   Production-ready

![Demo Screenshot](assets/demo_screenshot.png)

---

##  30-Second Quickstart

```bash
git clone https://github.com/rupac4530-creator/ai-desktop-assistant.git
cd ai-desktop-assistant
copy .env.example .env        # Configure your settings
.\run_assistant.bat           # Launch with overlay
```

**Requirements:** Python 3.10+  NVIDIA GPU (4GB+ VRAM)  Windows 10/11  [Ollama](https://ollama.ai)

---

##  Key Features

| Feature | What It Does | Tech Stack |
|---------|--------------|------------|
| ** Voice Control** | Real-time speech-to-text with GPU acceleration | Whisper, faster-whisper, CUDA |
| ** Local LLM** | Private AI conversations, no API keys needed | Ollama, Mistral, LLaMA |
| ** Text-to-Speech** | Natural voice responses | pyttsx3, SAPI5 |
| ** Self-Healing** | Auto-detects and fixes its own errors | Git-backed repair engine |

---

##  How to Demo (2 minutes)

1. **Start Ollama:** `ollama serve` (in separate terminal)
2. **Launch:** Double-click `run_assistant_with_overlay.bat`
3. **Speak:** Press `Ctrl+Shift+A`, say *"Open Chrome and search for Python tutorials"*
4. **Watch:** The assistant transcribes, thinks, and executes

**Demo commands to try:**
- *"What time is it?"*
- *"Open Notepad and type Hello World"*
- *"Search Google for machine learning"*

---

##  System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.10 | 3.11+ |
| **RAM** | 8 GB | 16 GB |
| **GPU VRAM** | 4 GB | 6+ GB |
| **Storage** | 5 GB | 10 GB |

---

##  Architecture

```

                     AI Desktop Assistant                     

   Speech         Brain         Core         Automation   
  (Whisper)     (Ollama)     (Watchdog)     (PyAutoGUI)   

              Self-Healing + Git-Backed Repair                

```

---

##  Project Structure

```
ai-desktop-assistant/
 speech/          # Whisper ASR + TTS
 brain/           # LLM client + memory
 core/            # Orchestration + self-healing
 automation/      # System control
 tools/           # Diagnostics + tests
 docs/            # Documentation
 assets/          # Demo assets
```

---

##  What Makes This Different

| Traditional Assistants | This Project |
|------------------------|--------------|
|  Cloud-dependent |  100% offline |
|  Sends your data to servers |  Zero data leaves your machine |
|  Requires API keys |  Free, local models |
|  Crashes and stays broken |  Self-healing with rollback |

---

##  Documentation

- [INSTALL.md](INSTALL.md) — Detailed setup instructions
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [ROADMAP.md](ROADMAP.md) — Future plans
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to contribute
- [FAQ](docs/FAQ.md) — Common questions

---

##  Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork, clone, create branch
git checkout -b feature/your-feature
# Make changes, test, commit
git commit -m "feat: add your feature"
# Push and create PR
git push origin feature/your-feature
```

---

##  Author

**Bedanta Chatterjee**

-  Email: [rupac4530@gmail.com](mailto:rupac4530@gmail.com)
-  GitHub: [@rupac4530-creator](https://github.com/rupac4530-creator)
-  Phone: +91 8617513035
-  Location: India

---

##  License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b> Star this repo if you find it useful!</b><br>
  <a href="https://github.com/rupac4530-creator/ai-desktop-assistant/releases/tag/v1.0.1">
    <img src="https://img.shields.io/badge/Download-v1.0.1-blue?style=for-the-badge" alt="Download v1.0.1">
  </a>
</p>
