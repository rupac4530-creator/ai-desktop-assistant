# Support

Need help with AI Desktop Assistant? Here's how to get support.

## 📖 Documentation

Before asking for help, please check:

1. **[README.md](README.md)** — Quick start guide
2. **[INSTALL.md](INSTALL.md)** — Detailed installation instructions
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design and internals
4. **[docs/FAQ.md](docs/FAQ.md)** — Frequently asked questions

## 🐛 Bug Reports

Found a bug? Please [open an issue](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=bug_report.md) with:

- Python version (`python --version`)
- OS and version
- GPU info (if applicable)
- Steps to reproduce
- Error messages (full traceback)

## 💡 Feature Requests

Have an idea? [Submit a feature request](https://github.com/rupac4530-creator/ai-desktop-assistant/issues/new?template=feature_request.md) with:

- Clear description of the feature
- Use case / motivation
- Any implementation ideas

## 💬 Discussions

For questions, ideas, or general discussion:

- **GitHub Issues** — For bugs and features
- **GitHub Discussions** — Coming soon!

## ⚡ Quick Troubleshooting

### "Ollama not running"
```bash
ollama serve
```

### "No audio frames captured"
- Check `MIC_DEVICE_INDEX` in `.env`
- Run `python -c "import sounddevice; print(sounddevice.query_devices())"` to list devices

### "CUDA out of memory"
- Use a smaller Whisper model: `WHISPER_MODEL=tiny.en` in `.env`
- Close other GPU applications

### "Model not found"
```bash
ollama pull mistral
```

### TTS not working
- Windows: Ensure SAPI5 voices are installed
- Linux: Install `espeak-ng` or `festival`

## 📧 Contact

For private matters or security issues:

- **Email**: rupac4530@gmail.com
- **Security**: See [SECURITY.md](SECURITY.md)

## ⏱️ Response Times

| Channel | Expected Response |
|---------|-------------------|
| Security issues | 24-48 hours |
| Bug reports | 1-3 days |
| Feature requests | 3-7 days |
| General questions | 1-5 days |

*Note: This is a solo maintainer project. Response times may vary.*

---

Thank you for using AI Desktop Assistant! 🚀
