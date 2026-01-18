# speech/local_tts.py
"""
Local TTS using pyttsx3 (Windows SAPI) with guaranteed audio playback.
Includes proper logging and avatar lip-sync support.
"""

import os
import threading
import time
from pathlib import Path
from datetime import datetime

# Logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
DEBUG_LOG = LOG_DIR / "last_session_debug.log"

def log_debug(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [TTS] {msg}\n")
    except:
        pass

# Try pyttsx3 for local TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    log_debug("pyttsx3 not available")

# Import avatar for lip-sync
try:
    from avatar import avatar_ws_client
    AVATAR_AVAILABLE = True
except ImportError:
    AVATAR_AVAILABLE = False


class LocalTTS:
    """Local text-to-speech using Windows SAPI via pyttsx3."""

    def __init__(self, rate=175, volume=1.0):
        self._engine = None
        self._lock = threading.Lock()
        self._speaking = False
        self._playback_complete = threading.Event()
        self.avatar = None
        self._speech_id = 0

        if PYTTSX3_AVAILABLE:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', rate)
                self._engine.setProperty('volume', volume)

                # List available voices
                voices = self._engine.getProperty('voices')
                if voices:
                    # Try to find a good English voice
                    for voice in voices:
                        if 'english' in voice.name.lower() or 'david' in voice.name.lower() or 'zira' in voice.name.lower():
                            self._engine.setProperty('voice', voice.id)
                            break

                print("[TTS] Local TTS ready (Windows SAPI)")
                log_debug("pyttsx3 engine initialized")
            except Exception as e:
                print(f"[TTS] Failed to initialize pyttsx3: {e}")
                log_debug(f"pyttsx3 init error: {e}")
                self._engine = None
        else:
            print("[TTS] pyttsx3 not available")

        # Get avatar client
        if AVATAR_AVAILABLE:
            try:
                self.avatar = avatar_ws_client.get_client()
            except:
                pass

    def _animate_mouth_loop(self, duration, speech_id):
        """Animate mouth while speaking."""
        if not self.avatar or not self.avatar.is_ready():
            return

        start = time.time()
        while time.time() - start < duration and self._speaking and self._speech_id == speech_id:
            for val in [0.7, 0.3, 0.5, 0.2, 0.6, 0.4]:
                if not self._speaking or self._speech_id != speech_id:
                    break
                try:
                    self.avatar.set_mouth_open(val)
                except:
                    pass
                time.sleep(0.08)

        try:
            self.avatar.set_mouth_open(0)
        except:
            pass

    def speak(self, text, block=True):
        """
        Speak text using local TTS.
        
        Args:
            text: Text to speak
            block: If True, wait for speech to complete (default True for guaranteed playback)
        """
        if not text or not text.strip():
            return

        text = text.strip()[:500]  # Limit length
        self._speech_id += 1
        current_id = self._speech_id
        
        print(f"[TTS] Speaking: {text[:50]}...")
        log_debug(f"Speaking (id={current_id}): {text[:100]}")

        def do_speak():
            with self._lock:
                self._speaking = True
                self._playback_complete.clear()
                start_time = time.time()
                log_debug(f"TTS playback started (id={current_id})")

                # Start mouth animation in background
                estimated_duration = len(text) * 0.06  # Rough estimate
                if self.avatar:
                    anim_thread = threading.Thread(
                        target=self._animate_mouth_loop,
                        args=(estimated_duration, current_id),
                        daemon=True
                    )
                    anim_thread.start()

                try:
                    if self._engine:
                        self._engine.say(text)
                        self._engine.runAndWait()
                    else:
                        # Fallback to PowerShell SAPI
                        self._speak_powershell(text)
                    
                    elapsed = time.time() - start_time
                    log_debug(f"TTS playback finished (id={current_id}): {elapsed:.1f}s")
                    print(f"[TTS] Finished speaking ({elapsed:.1f}s)")
                    
                except Exception as e:
                    print(f"[TTS] Error: {e}")
                    log_debug(f"TTS error (id={current_id}): {e}")
                finally:
                    self._speaking = False
                    self._playback_complete.set()
                    if self.avatar:
                        try:
                            self.avatar.set_mouth_open(0)
                        except:
                            pass

        if block:
            # Run in current thread for guaranteed completion
            do_speak()
        else:
            # Run in background
            threading.Thread(target=do_speak, daemon=True).start()

    def speak_async(self, text):
        """Speak text in background without blocking."""
        self.speak(text, block=False)

    def wait_for_completion(self, timeout=30.0):
        """Wait for current speech to complete."""
        return self._playback_complete.wait(timeout)

    def is_speaking(self):
        """Check if currently speaking."""
        return self._speaking

    def _speak_powershell(self, text):
        """Fallback using PowerShell SAPI."""
        import subprocess

        safe_text = text.replace('"', "'").replace('\n', ' ').replace('', "'")
        cmd = f'Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{safe_text}")'

        try:
            log_debug("Using PowerShell SAPI fallback")
            result = subprocess.run(
                ['powershell', '-Command', cmd], 
                capture_output=True, 
                timeout=60,
                text=True
            )
            if result.returncode != 0:
                log_debug(f"PowerShell error: {result.stderr}")
        except Exception as e:
            print(f"[TTS] PowerShell fallback failed: {e}")
            log_debug(f"PowerShell fallback error: {e}")

    def set_rate(self, rate):
        """Set speech rate (words per minute)."""
        if self._engine:
            self._engine.setProperty('rate', rate)

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)."""
        if self._engine:
            self._engine.setProperty('volume', max(0.0, min(1.0, volume)))

    def list_voices(self):
        """List available voices."""
        if self._engine:
            voices = self._engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name} for v in voices]
        return []

    def set_voice(self, voice_id):
        """Set voice by ID."""
        if self._engine:
            self._engine.setProperty('voice', voice_id)


# Singleton instance
_instance = None
_instance_lock = threading.Lock()

def get_tts():
    """Get singleton TTS instance (thread-safe)."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = LocalTTS()
    return _instance

def speak(text, block=True):
    """Convenience function to speak text."""
    get_tts().speak(text, block=block)

def speak_async(text):
    """Convenience function to speak text without blocking."""
    get_tts().speak_async(text)
