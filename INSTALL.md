# Installation Guide

Complete step-by-step installation instructions for the AI Desktop Assistant.

---

## Prerequisites

### Required Software

1. **Windows 10/11 (64-bit)**
   - Windows 10 version 1903 or later
   - Windows 11 any version

2. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - âœ… Check "Add Python to PATH" during installation

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/download/win)
   - Or install via: `winget install Git.Git`

4. **Microphone**
   - Any USB or built-in microphone
   - Ensure Windows microphone permissions are enabled

### Optional (Recommended)

5. **NVIDIA GPU with CUDA**
   - For faster speech recognition (10x speed improvement)
   - Requires: NVIDIA driver 520+ and CUDA Toolkit 11.8+
   - Without GPU: CPU mode works but is slower

6. **Ollama** (for local LLM)
   - Download from [ollama.ai](https://ollama.ai/)
   - Provides local AI reasoning without cloud API

---

## Installation Steps

### Step 1: Clone the Repository

```powershell
git clone https://github.com/yourusername/ai-desktop-assistant.git
cd ai-desktop-assistant
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies

```powershell
# Core dependencies
pip install -r requirements.txt

# Optional: CUDA support for faster STT (requires NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Step 4: Configure Environment

```powershell
# Copy the example environment file
copy .env.example .env

# Edit with your settings
notepad .env
```

**Required settings in `.env`:**
```ini
# Device configuration
DEVICE=cuda              # Use 'cpu' if no NVIDIA GPU

# Speech settings
STT_MODEL=large-v2       # Options: tiny, base, small, medium, large-v2
TTS_VOICE=en_US-amy-medium

# Autonomy settings
FULL_AUTONOMY=true
SELF_HEAL_ENABLED=true
```

**Optional API keys (only if using cloud services):**
```ini
OPENAI_API_KEY=your_key_here    # For GPT-4 (optional)
```

### Step 5: Install Ollama Models (Recommended)

```powershell
# Install Ollama from https://ollama.ai first, then:
ollama pull mistral:7b-instruct
ollama pull llama3:latest
ollama pull codellama:7b-instruct
```

### Step 6: Download TTS Voice Model

```powershell
# Create models directory
mkdir models\piper -Force

# Download voice model (example: Amy voice)
# Models available at: https://github.com/rhasspy/piper/releases
```

### Step 7: Verify Installation

```powershell
# Activate environment
.\venv\Scripts\activate

# Run system check
python tools/system_check.py

# Run tests
python -m pytest tools/test_core_smoke.py -v
```

---

## Running the Assistant

### Start the Assistant

```powershell
cd E:\ai_desktop_assistant
.\venv\Scripts\activate
python core/main_controller.py
```

### Quick Start Script

Create a `start.bat` file for easy launching:
```batch
@echo off
cd /d E:\ai_desktop_assistant
call venv\Scripts\activate
python core\main_controller.py
```

### Run at Startup (Optional)

1. Press `Win+R`, type `shell:startup`
2. Create a shortcut to `start.bat` in that folder

---

## Troubleshooting

### "No audio frames" Error

1. Check Windows microphone permissions:
   - Settings â†’ Privacy â†’ Microphone â†’ Enable
2. Run microphone diagnostics:
   ```powershell
   python tools/mic_diagnostics.py
   ```

### CUDA Not Detected

1. Verify NVIDIA driver: `nvidia-smi`
2. Check PyTorch CUDA: 
   ```python
   import torch; print(torch.cuda.is_available())
   ```
3. Reinstall PyTorch with CUDA:
   ```powershell
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

### Ollama Connection Failed

1. Ensure Ollama is running: `ollama serve`
2. Check port 11434 is accessible
3. Test with: `curl http://localhost:11434/api/tags`

### TTS Not Working

1. Check Piper model is downloaded to `models/piper/`
2. Verify audio output device in Windows Sound settings

---

## Updating

```powershell
cd E:\ai_desktop_assistant
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## Uninstallation

```powershell
# Remove the project directory
Remove-Item -Recurse -Force E:\ai_desktop_assistant

# Optional: Remove Ollama models
ollama rm mistral:7b-instruct
ollama rm llama3:latest
```

---

## Support

If you encounter issues:
1. Check the [troubleshooting section](#troubleshooting)
2. Review logs in `logs/` directory
3. Open an issue on GitHub with:
   - Error message
   - `logs/last_session_debug.log` contents
   - System info (Windows version, Python version, GPU)

