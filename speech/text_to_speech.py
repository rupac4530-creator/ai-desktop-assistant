# speech/text_to_speech.py
"""Text-to-speech with ElevenLabs (cloud) or local (pyttsx3) support."""

import os
import io
import requests
import threading
import time

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None

from avatar import avatar_ws_client

# Configuration
TTS_MODE = os.getenv('TTS_MODE', 'local')  # 'local' or 'elevenlabs'
ELEVEN_KEY = os.getenv('ELEVENLABS_API_KEY')
VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
MODEL_ID = "eleven_multilingual_v2"


class TextToSpeech:
    def __init__(self):
        self.avatar = avatar_ws_client.get_client()
        self._speaking = False
        self._local_tts = None
        
        # Initialize local TTS if needed
        if TTS_MODE == 'local' or not ELEVEN_KEY:
            try:
                from speech.local_tts import LocalTTS
                self._local_tts = LocalTTS()
                print("[TTS] Using local TTS (Windows SAPI)")
            except Exception as e:
                print(f"[TTS] Local TTS init failed: {e}")

    def _animate_mouth_loop(self, audio_duration):
        """Animate mouth open/close while speaking."""
        if not self.avatar.is_ready():
            return
        
        start = time.time()
        while time.time() - start < audio_duration and self._speaking:
            for val in [0.8, 0.3, 0.6, 0.2, 0.7, 0.4]:
                if not self._speaking:
                    break
                self.avatar.set_mouth_open(val)
                time.sleep(0.08)
        self.avatar.set_mouth_open(0)

    def speak(self, text, lang='en'):
        if not text or not text.strip():
            return

        print(f"[TTS] Speaking: {text[:50]}...")

        # Use local TTS if configured or no API key
        if TTS_MODE == 'local' or not ELEVEN_KEY:
            if self._local_tts:
                self._local_tts.speak(text)
            else:
                self._fallback_speak(text)
            return

        # Use ElevenLabs
        try:
            url = f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}'
            headers = {
                'xi-api-key': ELEVEN_KEY,
                'Content-Type': 'application/json',
                'Accept': 'audio/mpeg'
            }
            payload = {
                'text': text,
                'model_id': MODEL_ID,
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.75
                }
            }

            resp = requests.post(url, json=payload, headers=headers, timeout=30)

            if resp.status_code != 200:
                print(f"[TTS] ElevenLabs error {resp.status_code}: {resp.text[:100]}")
                self._fallback_speak(text)
                return

            audio_data = resp.content
            self._play_audio_with_lipsync(audio_data)

        except Exception as e:
            print(f"[TTS] Error: {e}")
            self._fallback_speak(text)

    def _play_audio_with_lipsync(self, audio_data):
        """Play audio and animate avatar."""
        import tempfile

        self._speaking = True

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            if pygame:
                pygame.mixer.music.load(temp_path)
                duration = max(2, len(audio_data) / 15000)

                anim_thread = threading.Thread(target=self._animate_mouth_loop, args=(duration,))
                anim_thread.start()

                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                self._speaking = False
                anim_thread.join(timeout=1)
            else:
                import subprocess
                subprocess.run(['powershell', '-c',
                    f'Add-Type -AssemblyName presentationCore; ' +
                    f'\ = New-Object System.Windows.Media.MediaPlayer; ' +
                    f'\.Open(\"{temp_path}\"); \.Play(); Start-Sleep -s 5'
                ], capture_output=True)
        finally:
            self._speaking = False
            if self.avatar.is_ready():
                self.avatar.set_mouth_open(0)
            try:
                os.unlink(temp_path)
            except:
                pass

    def _fallback_speak(self, text):
        """Windows SAPI fallback."""
        import subprocess
        self._speaking = True

        anim_thread = threading.Thread(target=self._animate_mouth_loop, args=(len(text) * 0.05,))
        anim_thread.start()

        safe_text = text.replace('"', "'").replace('\n', ' ')[:500]
        cmd = f'Add-Type -AssemblyName System.Speech; \ = New-Object System.Speech.Synthesis.SpeechSynthesizer; \.Speak(\"{safe_text}\")'

        try:
            subprocess.run(['powershell', '-Command', cmd], capture_output=True, timeout=30)
        except:
            pass
        finally:
            self._speaking = False
            anim_thread.join(timeout=1)
            if self.avatar.is_ready():
                self.avatar.set_mouth_open(0)


# Convenience function
def speak(text, lang='en'):
    tts = TextToSpeech()
    tts.speak(text, lang)
