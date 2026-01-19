# Frequently Asked Questions

## 🎤 Audio & Speech

### Q: Why isn't my microphone being detected?
**A:** Run this to list all audio devices:
```bash
python -c "import sounddevice; print(sounddevice.query_devices())"
```
Find your microphone's index number and set `MIC_DEVICE_INDEX` in your `.env` file.

### Q: Why does transcription say "No audio frames captured"?
**A:** This usually means:
1. Wrong microphone selected — Check `MIC_DEVICE_INDEX`
2. Microphone is muted in Windows/OS settings
3. Another app has exclusive access to the mic

### Q: Can I use a USB microphone?
**A:** Yes! Just find its device index and update `.env`. USB mics often work better than laptop built-in mics.

### Q: Why is transcription slow?
**A:** Try these fixes:
- Use a smaller model: `WHISPER_MODEL=tiny.en`
- Ensure CUDA is enabled: `DEVICE=cuda`
- Check GPU memory with `nvidia-smi`

---

## 🤖 AI & Models

### Q: Which LLM should I use?
**A:** Recommended models by VRAM:
| VRAM | Model | Set in .env |
|------|-------|-------------|
| 4GB | Phi-3 Mini | `OLLAMA_MODEL=phi3` |
| 6GB | Mistral 7B | `OLLAMA_MODEL=mistral` |
| 8GB+ | Llama 3 8B | `OLLAMA_MODEL=llama3` |

### Q: Why is the AI response slow?
**A:** LLM inference is GPU-intensive. Tips:
- Use a smaller model
- Close other GPU applications
- Ensure Ollama is using CUDA (not CPU)

### Q: Can I use OpenAI API instead of Ollama?
**A:** Not currently, but this is on the [roadmap](ROADMAP.md) for v1.2.

### Q: How do I change the AI's personality?
**A:** Modify the system prompt in `core/orchestrator.py`.

---

## 🖥️ System & Performance

### Q: Does this work on Linux/Mac?
**A:** Currently Windows-only. Linux support is planned for v1.1.

### Q: How much RAM/VRAM do I need?
**A:** Minimum recommended:
- RAM: 8GB (16GB recommended)
- VRAM: 4GB for small models, 6GB+ for Mistral

### Q: Why do I get "CUDA out of memory"?
**A:** Your GPU is running out of VRAM. Try:
1. Close other GPU applications
2. Use a smaller Whisper model
3. Use a smaller LLM

### Q: Can I run this on CPU only?
**A:** Yes, set `DEVICE=cpu` in `.env`. It will be slower but functional.

---

## 🔒 Privacy & Security

### Q: Does this send my data to the internet?
**A:** No! Everything runs 100% locally:
- Whisper runs on your GPU
- Ollama runs on your machine
- No telemetry or analytics

### Q: Are my conversations stored?
**A:** Conversation history is kept in memory during a session and cleared on exit. No persistent logs unless you enable them.

### Q: Is it safe to run system commands?
**A:** The assistant asks for confirmation before running commands. You can also disable command execution in settings.

---

## 🛠️ Installation

### Q: I get "cublas64_12.dll not found"
**A:** Install CUDA libraries:
```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### Q: Ollama won't start
**A:** 
1. Download from https://ollama.ai
2. Run `ollama serve` in a terminal
3. Pull a model: `ollama pull mistral`

### Q: pip install fails with build errors
**A:** Some packages need build tools:
- Windows: Install Visual Studio Build Tools
- Linux: `sudo apt install build-essential`

---

## 🎮 Usage

### Q: What are the keyboard shortcuts?
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+A` | Start recording |
| `Ctrl+Shift+S` | Stop recording |
| `Ctrl+Shift+Q` | Quit application |

### Q: Can I use push-to-talk?
**A:** Yes! Hold `Ctrl+Shift+A` to record, release to process.

### Q: How do I clear the conversation?
**A:** Say "clear history" or "forget everything" or restart the app.

---

## 📦 Development

### Q: How do I add a new plugin?
**A:** See [ARCHITECTURE.md](ARCHITECTURE.md) for the plugin system design.

### Q: How do I contribute?
**A:** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Q: Where do I report bugs?
**A:** Open an issue on [GitHub](https://github.com/rupac4530-creator/ai-desktop-assistant/issues).

---

## 🆘 Still Need Help?

1. Check [GitHub Issues](https://github.com/rupac4530-creator/ai-desktop-assistant/issues)
2. Read [SUPPORT.md](../SUPPORT.md)
3. Email: rupac4530@gmail.com
