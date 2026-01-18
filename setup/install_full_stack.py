# setup/install_full_stack.py
"""
Complete setup script for AI Desktop Assistant - Full Local Stack
Installs and configures: Ollama, faster-whisper, Coqui TTS, Playwright, Tesseract
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VENV_PATH = PROJECT_ROOT / "venv"
PYTHON = VENV_PATH / "Scripts" / "python.exe"
PIP = VENV_PATH / "Scripts" / "pip.exe"


def run_cmd(cmd, check=True, shell=True):
    """Run a command and return output."""
    print(f"  > {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    return result


def check_command_exists(cmd):
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None


def install_python_packages():
    """Install all required Python packages."""
    print("\n[1/7] Installing Python packages...")
    
    packages = [
        # Core
        "python-dotenv",
        "requests",
        "websocket-client",
        "pystray",
        "pillow",
        "keyboard",
        
        # Speech
        "faster-whisper",
        "pyaudio",
        "pygame",
        
        # Vision
        "mss",
        "opencv-python-headless",
        "pytesseract",
        
        # Automation
        "playwright",
        "pyautogui",
        "GitPython",
        "aiohttp",
        
        # LLM
        "ollama",
    ]
    
    # Install packages
    run_cmd(f'"{PIP}" install --upgrade pip')
    run_cmd(f'"{PIP}" install {" ".join(packages)}')
    
    # Install Playwright browsers
    print("  Installing Playwright browsers...")
    run_cmd(f'"{PYTHON}" -m playwright install chromium')
    
    print("  ✓ Python packages installed")


def check_ollama():
    """Check if Ollama is installed and running."""
    print("\n[2/7] Checking Ollama...")
    
    if not check_command_exists("ollama"):
        print("  Ollama not found. Please install from: https://ollama.ai/download")
        print("  After installing, run: ollama pull llama3:8b")
        return False
    
    # Check if ollama is running
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m['name'] for m in data.get('models', [])]
            print(f"  Ollama running. Available models: {models}")
            
            # Check for recommended models
            recommended = ['llama3:8b', 'llama3', 'qwen2.5', 'qwen2.5:7b']
            found = [m for m in recommended if any(m in model for model in models)]
            
            if not found:
                print(f"  No recommended model found. Run: ollama pull llama3:8b")
            else:
                print(f"  ✓ Found model: {found[0]}")
            return True
    except Exception as e:
        print(f"  Ollama not running. Start it with: ollama serve")
        return False


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    print("\n[3/7] Checking Tesseract OCR...")
    
    if check_command_exists("tesseract"):
        result = run_cmd("tesseract --version", check=False)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"  ✓ Tesseract installed: {version}")
            return True
    
    print("  Tesseract not found.")
    print("  Install via: choco install -y tesseract")
    print("  Or download from: https://github.com/tesseract-ocr/tesseract/releases")
    return False


def check_autohotkey():
    """Check if AutoHotkey is installed."""
    print("\n[4/7] Checking AutoHotkey...")
    
    ahk_paths = [
        r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
        r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe",
    ]
    
    for path in ahk_paths:
        if os.path.exists(path):
            print(f"  ✓ AutoHotkey found: {path}")
            return True
    
    if check_command_exists("autohotkey"):
        print("  ✓ AutoHotkey found in PATH")
        return True
    
    print("  AutoHotkey not found.")
    print("  Install via: winget install --id AutoHotkey.AutoHotkey -e")
    return False


def check_vb_cable():
    """Check if VB-Audio Cable is installed."""
    print("\n[5/7] Checking VB-Audio Cable...")
    
    # Check for VB-Cable in audio devices
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        vb_found = False
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if 'CABLE' in info['name'].upper() or 'VB-AUDIO' in info['name'].upper():
                print(f"  ✓ VB-Cable found: {info['name']}")
                vb_found = True
                break
        
        p.terminate()
        
        if not vb_found:
            print("  VB-Audio Cable not found.")
            print("  Download from: https://vb-audio.com/Cable/")
            return False
        return True
    except Exception as e:
        print(f"  Could not check audio devices: {e}")
        return False


def check_vtube_studio():
    """Check VTube Studio configuration."""
    print("\n[6/7] Checking VTube Studio...")
    
    # Try to connect to VTS WebSocket
    try:
        import websocket
        ws = websocket.create_connection("ws://127.0.0.1:8001", timeout=3)
        ws.close()
        print("  ✓ VTube Studio WebSocket accessible on port 8001")
        return True
    except Exception as e:
        print("  VTube Studio not running or WebSocket not enabled.")
        print("  Open VTube Studio and enable: Settings > General > Start API")
        return False


def setup_local_tts():
    """Set up local TTS (Coqui or pyttsx3 fallback)."""
    print("\n[7/7] Setting up Local TTS...")
    
    # Try to install Coqui TTS
    try:
        result = run_cmd(f'"{PIP}" install TTS', check=False)
        if result.returncode == 0:
            print("  ✓ Coqui TTS installed")
            
            # Create TTS wrapper
            create_local_tts_module()
            return True
    except Exception as e:
        print(f"  Coqui TTS install failed: {e}")
    
    # Fallback to pyttsx3
    print("  Falling back to pyttsx3...")
    run_cmd(f'"{PIP}" install pyttsx3')
    print("  ✓ pyttsx3 installed (Windows SAPI)")
    return True


def create_local_tts_module():
    """Create a local TTS module that uses Coqui or fallback."""
    tts_path = PROJECT_ROOT / "speech" / "local_tts.py"
    
    content = '''# speech/local_tts.py
"""Local TTS using Coqui TTS or pyttsx3 fallback."""

import os
import tempfile
import threading
import time

# Try Coqui TTS first
try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False

# Fallback to pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False


class LocalTTS:
    """Local text-to-speech with Coqui or pyttsx3."""
    
    def __init__(self, use_coqui=True, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        self.use_coqui = use_coqui and COQUI_AVAILABLE
        self._tts = None
        self._pyttsx_engine = None
        self._lock = threading.Lock()
        
        if self.use_coqui:
            try:
                print("[TTS] Loading Coqui TTS model (first run may download)...")
                self._tts = TTS(model_name=model_name, progress_bar=False)
                print("[TTS] Coqui TTS ready")
            except Exception as e:
                print(f"[TTS] Coqui failed: {e}, falling back to pyttsx3")
                self.use_coqui = False
        
        if not self.use_coqui and PYTTSX3_AVAILABLE:
            self._pyttsx_engine = pyttsx3.init()
            self._pyttsx_engine.setProperty('rate', 175)
            print("[TTS] Using pyttsx3 (Windows SAPI)")
    
    def speak(self, text, output_device=None):
        """Speak text using local TTS."""
        if not text or not text.strip():
            return
        
        text = text.strip()[:500]  # Limit length
        print(f"[TTS] Speaking: {text[:50]}...")
        
        with self._lock:
            if self.use_coqui:
                self._speak_coqui(text, output_device)
            elif self._pyttsx_engine:
                self._speak_pyttsx(text)
            else:
                print("[TTS] No TTS engine available")
    
    def _speak_coqui(self, text, output_device=None):
        """Speak using Coqui TTS."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name
            
            self._tts.tts_to_file(text=text, file_path=temp_path)
            
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            
            try:
                os.unlink(temp_path)
            except:
                pass
        except Exception as e:
            print(f"[TTS] Coqui error: {e}")
            if self._pyttsx_engine:
                self._speak_pyttsx(text)
    
    def _speak_pyttsx(self, text):
        """Speak using pyttsx3."""
        try:
            self._pyttsx_engine.say(text)
            self._pyttsx_engine.runAndWait()
        except Exception as e:
            print(f"[TTS] pyttsx3 error: {e}")


# Singleton instance
_instance = None

def get_tts():
    global _instance
    if _instance is None:
        _instance = LocalTTS()
    return _instance

def speak(text):
    get_tts().speak(text)
'''
    
    with open(tts_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  Created: {tts_path}")


def create_env_template():
    """Create .env template if not exists."""
    env_path = PROJECT_ROOT / ".env"
    
    if env_path.exists():
        print("\n.env file already exists")
        return
    
    content = '''# AI Desktop Assistant Configuration

# LLM (Ollama)
OLLAMA_MODEL=llama3:8b
OLLAMA_URL=http://localhost:11434

# Speech-to-Text (faster-whisper)
WHISPER_MODEL=base
# Options: tiny, base, small, medium, large-v2

# Text-to-Speech
# Set to "local" to use Coqui/pyttsx3, or "elevenlabs" for cloud
TTS_MODE=local
# If using ElevenLabs (optional, requires API key)
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# VB-Cable device name (for routing to VTube Studio)
TTS_OUTPUT_DEVICE=CABLE Input

# VTube Studio
AVATAR_WS_URL=ws://127.0.0.1:8001

# Safety
REQUIRE_CONFIRMATION_FOR_DANGEROUS=true
CONFIRMATION_TIMEOUT_SECONDS=5
'''
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nCreated: {env_path}")


def create_launcher_scripts():
    """Create convenient launcher scripts."""
    
    # PowerShell launcher
    ps_launcher = PROJECT_ROOT / "start_assistant.ps1"
    ps_content = '''# Start AI Desktop Assistant
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

# Activate venv
& "$ROOT\\venv\\Scripts\\Activate.ps1"

# Set PYTHONPATH
$env:PYTHONPATH = $ROOT

# Start Ollama if not running
$ollamaRunning = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "Starting Ollama..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# Start AutoHotkey overlay
$ahkPath = "$ROOT\\tools\\vt_overlay.ahk"
if (Test-Path $ahkPath) {
    Start-Process -FilePath "C:\\Program Files\\AutoHotkey\\AutoHotkey.exe" -ArgumentList $ahkPath -WindowStyle Hidden
}

# Run assistant
python "$ROOT\\core\\main_controller.py"
'''
    
    with open(ps_launcher, 'w', encoding='utf-8') as f:
        f.write(ps_content)
    print(f"Created: {ps_launcher}")
    
    # Batch launcher
    bat_launcher = PROJECT_ROOT / "start_assistant.bat"
    bat_content = '''@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0start_assistant.ps1"
'''
    
    with open(bat_launcher, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"Created: {bat_launcher}")


def print_summary(results):
    """Print setup summary."""
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    for name, status in results.items():
        icon = "✓" if status else "✗"
        print(f"  {icon} {name}")
    
    print("\n" + "-" * 60)
    
    if all(results.values()):
        print("All components ready! Run: .\\start_assistant.bat")
    else:
        print("Some components need manual setup. See notes above.")
    
    print("-" * 60)
    print("""
NEXT STEPS:
1. If Ollama not installed: https://ollama.ai/download
   Then run: ollama pull llama3:8b

2. If VB-Cable not installed: https://vb-audio.com/Cable/

3. If VTube Studio not configured:
   - Open VTube Studio
   - Go to Settings > General > Start API (port 8001)
   - Set microphone input to "CABLE Output"

4. Run the assistant:
   .\\start_assistant.bat
   
5. Hotkeys:
   - Ctrl+Alt+Space : Push-to-talk
   - Ctrl+Alt+T     : Type command
   - Ctrl+Alt+H     : Show/hide avatar
   - Ctrl+Alt+A     : Toggle click-through
""")


def main():
    print("=" * 60)
    print("AI Desktop Assistant - Full Local Stack Setup")
    print("=" * 60)
    
    results = {}
    
    # Install Python packages
    install_python_packages()
    results['Python packages'] = True
    
    # Check external tools
    results['Ollama'] = check_ollama()
    results['Tesseract OCR'] = check_tesseract()
    results['AutoHotkey'] = check_autohotkey()
    results['VB-Audio Cable'] = check_vb_cable()
    results['VTube Studio'] = check_vtube_studio()
    
    # Setup local TTS
    results['Local TTS'] = setup_local_tts()
    
    # Create config files
    create_env_template()
    create_launcher_scripts()
    
    # Summary
    print_summary(results)


if __name__ == "__main__":
    main()
