# ui/keyboard.py
"""
Keyboard hotkey handler with toggle PTT + Enter stop support.
Proper PTT state reset after each command to accept new recordings.
"""

import os
import threading
import time
import tkinter as tk
from tkinter import simpledialog
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
            f.write(f"[{ts}] [Keyboard] {msg}\n")
    except:
        pass

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    keyboard = None
    KEYBOARD_AVAILABLE = False

# Configuration
PTT_MODE = os.getenv("PTT_MODE", "toggle")
PTT_HOTKEY = os.getenv("PTT_HOTKEY", "ctrl+alt+space")
PTT_STOP_KEY = os.getenv("PTT_STOP_KEY", "Enter").lower()
TYPE_HOTKEY = os.getenv("TYPE_HOTKEY", "ctrl+alt+t")


class KeyboardListener:
    """
    Keyboard listener with toggle PTT + Enter stop support.
    Properly resets state after each command for continuous use.
    """

    def __init__(self, callback, asr_engine):
        self.callback = callback
        self.asr = asr_engine
        self.ptt_mode = PTT_MODE
        self._running = False
        self._lock = threading.Lock()
        self._transcribing = False
        self._enter_hook = None
        self._ready_for_ptt = True  # New: explicit ready state

        # TTS for feedback
        self._tts = None
        try:
            from speech.local_tts import get_tts
            self._tts = get_tts()
        except:
            pass

        # HUD for visual feedback
        self._hud = None
        try:
            from ui.hud import get_hud
            self._hud = get_hud()
        except:
            pass
        
        log_debug("KeyboardListener initialized")

    def _speak(self, text):
        """Speak using TTS if available."""
        if self._tts:
            try:
                self._tts.speak(text, block=False)  # Non-blocking for responsiveness
            except:
                pass

    def _update_hud(self, listening=None, error=None, message=None):
        """Update HUD status."""
        if self._hud:
            try:
                if listening is not None:
                    self._hud.set_listening(listening)
                if error:
                    self._hud.set_error(error)
                if message:
                    self._hud.set_message(message)
            except:
                pass

    def _open_input_box(self):
        """Open a dialog for typed input."""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            answer = simpledialog.askstring("AI Assistant", "Type a command:", parent=root)
            root.destroy()
            if answer and answer.strip():
                print(f'[Keyboard] Typed: {answer.strip()}')
                log_debug(f"Typed input: {answer.strip()}")
                self.callback(answer.strip())
        except Exception as e:
            print(f"[Keyboard] Input dialog error: {e}")
            log_debug(f"Input dialog error: {e}")

    def _start_enter_listener(self):
        """Start global Enter key listener (only while recording)."""
        if not KEYBOARD_AVAILABLE:
            return
        try:
            self._stop_enter_listener()
            self._enter_hook = keyboard.on_press_key(
                "enter",
                lambda e: self._on_enter_pressed(),
                suppress=False
            )
            print("[Keyboard] Enter listener active (press Enter to stop recording)")
            log_debug("Enter listener registered")
        except Exception as e:
            print(f"[Keyboard] Could not register Enter listener: {e}")
            log_debug(f"Enter listener error: {e}")

    def _stop_enter_listener(self):
        """Stop global Enter key listener."""
        if self._enter_hook:
            try:
                keyboard.unhook(self._enter_hook)
            except:
                pass
            self._enter_hook = None
            log_debug("Enter listener unregistered")

    def _on_enter_pressed(self):
        """Handle Enter key press while recording."""
        with self._lock:
            if self.asr.is_recording() and not self._transcribing:
                print("[Keyboard] Enter pressed - stopping recording...")
                log_debug("Enter pressed - stopping recording")
                self._do_stop_and_transcribe()

    def _on_ptt_toggle(self):
        """Handle PTT toggle (Ctrl+Alt+Space in toggle mode)."""
        with self._lock:
            # Check if we're busy
            if self._transcribing:
                print("[Keyboard] Busy transcribing, ignoring PTT")
                log_debug("PTT ignored - transcribing")
                self._update_hud(message="Still processing previous command...")
                return

            if self.asr.is_recording():
                # Already recording - stop and transcribe
                print("[Keyboard] PTT toggle OFF - stopping recording...")
                log_debug("PTT toggle OFF")
                self._do_stop_and_transcribe()
            else:
                # Check if ready
                if not self._ready_for_ptt:
                    print("[Keyboard] Not ready for PTT yet")
                    log_debug("PTT ignored - not ready")
                    self._update_hud(message="Still processing...")
                    return
                    
                # Start recording
                print("[Keyboard] PTT toggle ON - recording...")
                log_debug("PTT toggle ON - recording started")
                self._ready_for_ptt = False
                self._update_hud(listening=True, message="Recording - press Enter or Ctrl+Alt+Space to stop")
                
                if not self.asr.start_recording():
                    print("[Keyboard] Failed to start recording")
                    log_debug("Failed to start recording")
                    self._ready_for_ptt = True
                    self._update_hud(listening=False, error="Failed to start recording")
                    return
                    
                # Start Enter listener
                self._start_enter_listener()
                # Start mic health check
                threading.Thread(target=self._check_mic_health, daemon=True).start()

    def _check_mic_health(self):
        """Check for mic issues (no audio within 2s of starting)."""
        time.sleep(2.0)
        with self._lock:
            if self.asr.is_recording() and not self._transcribing:
                if hasattr(self.asr, '_frames') and len(self.asr._frames) < 5:
                    print("[Keyboard] Mic health check: No audio frames detected!")
                    log_debug("Mic health check failed")
                    self._stop_enter_listener()
                    self.asr.stop_recording()
                    self._speak("I can't access the microphone. Check permissions.")
                    self._update_hud(listening=False, error="Mic access failed")
                    self._ready_for_ptt = True
                    self._transcribing = False

    def _on_ptt_hold_down(self):
        """Handle PTT key press in hold mode."""
        with self._lock:
            if self._transcribing or self.asr.is_recording():
                return
            if not self._ready_for_ptt:
                return
            print("[Keyboard] PTT pressed - recording...")
            log_debug("PTT hold down - recording")
            self._ready_for_ptt = False
            self._update_hud(listening=True, message="Recording - release to stop")
            self.asr.start_recording()

    def _on_ptt_hold_up(self):
        """Handle PTT key release in hold mode."""
        with self._lock:
            if self.asr.is_recording() and not self._transcribing:
                print("[Keyboard] PTT released - stopping...")
                log_debug("PTT hold up - stopping")
                self._do_stop_and_transcribe()

    def _do_stop_and_transcribe(self):
        """Stop recording and transcribe in background thread."""
        # Stop Enter listener first
        self._stop_enter_listener()
        
        self._transcribing = True
        self._update_hud(listening=False, message="Transcribing...")
        log_debug("Transcription starting")

        def transcribe_async():
            try:
                duration = self.asr.get_recording_duration()
                print(f"[Keyboard] Stopping after {duration:.1f}s...")
                log_debug(f"Recording duration: {duration:.1f}s")

                text, confidence = self.asr.stop_and_transcribe()
                
                log_debug(f"Transcription result: conf={confidence:.2f}, text='{text[:50]}...'")

                if not text or not text.strip():
                    print("[Keyboard] No speech detected")
                    self._speak("I didn't catch that. Please repeat.")
                    self._update_hud(error="No speech detected", message=None)
                elif confidence < self.asr.confidence_threshold:
                    print(f"[Keyboard] Low confidence: {confidence:.2f}")
                    self._speak("I didn't catch that. Please repeat.")
                    self._update_hud(message=f"Low confidence: {text[:50]}...", error=None)
                else:
                    print(f"[Keyboard] Transcribed: {text}")
                    self._update_hud(message=f"You said: {text[:100]}", error=None)
                    # Call the callback with transcribed text
                    try:
                        self.callback(text.strip())
                    except Exception as e:
                        print(f"[Keyboard] Callback error: {e}")
                        log_debug(f"Callback error: {e}")
                        self._speak("Sorry, I had an error processing that.")
                        
            except Exception as e:
                print(f"[Keyboard] Transcription error: {e}")
                log_debug(f"Transcription error: {e}")
                self._speak("Sorry, transcription failed.")
                self._update_hud(error=str(e), message=None)
            finally:
                # CRITICAL: Reset state to allow new recordings
                with self._lock:
                    self._transcribing = False
                    self._ready_for_ptt = True
                log_debug("PTT state reset - ready for new recording")
                print("[Keyboard] Ready for new recording")

        threading.Thread(target=transcribe_async, daemon=True).start()

    def _on_type_hotkey(self):
        """Handle type hotkey (Ctrl+Alt+T)."""
        print('[Keyboard] Type hotkey pressed')
        log_debug("Type hotkey pressed")
        threading.Thread(target=self._open_input_box, daemon=True).start()

    def _check_modifiers_and_ptt_down(self):
        """Check if modifiers are held and trigger PTT down (hold mode)."""
        try:
            if keyboard.is_pressed('ctrl') and keyboard.is_pressed('alt'):
                self._on_ptt_hold_down()
        except:
            pass

    def _check_modifiers_and_ptt_up(self):
        """Check modifiers and trigger PTT up (hold mode)."""
        try:
            if self.asr.is_recording():
                self._on_ptt_hold_up()
        except:
            pass

    def reset_state(self):
        """Reset PTT state for re-initialization."""
        with self._lock:
            self._transcribing = False
            self._ready_for_ptt = True
            self._stop_enter_listener()
        log_debug("State reset manually")

    def start(self):
        """Start listening for hotkeys."""
        if not KEYBOARD_AVAILABLE:
            print("[Keyboard] keyboard library not available")
            return False

        if self._running:
            return True

        self._running = True
        self._ready_for_ptt = True
        log_debug("Keyboard listener starting")

        # Register type hotkey
        try:
            keyboard.add_hotkey(TYPE_HOTKEY, self._on_type_hotkey, suppress=False)
            print(f'[Keyboard] {TYPE_HOTKEY} registered (type command)')
        except Exception as e:
            print(f'[Keyboard] Failed to register {TYPE_HOTKEY}: {e}')

        # Register PTT hotkey based on mode
        try:
            if self.ptt_mode == "hold":
                keyboard.on_press_key(
                    PTT_HOTKEY.split("+")[-1],
                    lambda e: self._check_modifiers_and_ptt_down(),
                    suppress=False
                )
                keyboard.on_release_key(
                    PTT_HOTKEY.split("+")[-1],
                    lambda e: self._check_modifiers_and_ptt_up(),
                    suppress=False
                )
                print(f'[Keyboard] {PTT_HOTKEY} registered (hold-to-record)')
            else:
                keyboard.add_hotkey(PTT_HOTKEY, self._on_ptt_toggle, suppress=False)
                print(f'[Keyboard] {PTT_HOTKEY} registered (toggle mode)')
                print(f'[Keyboard] Enter will stop recording when active')
        except Exception as e:
            print(f'[Keyboard] Failed to register PTT: {e}')
            try:
                keyboard.add_hotkey(PTT_HOTKEY, self._on_ptt_toggle, suppress=False)
                print(f'[Keyboard] {PTT_HOTKEY} registered (fallback toggle)')
            except Exception as e2:
                print(f'[Keyboard] Fallback failed: {e2}')

        mode_str = "hold-to-record" if self.ptt_mode == "hold" else "toggle+Enter"
        print(f'[Keyboard] Ready! PTT mode: {mode_str}')
        log_debug(f"Listener ready, mode={mode_str}")
        return True

    def stop(self):
        """Stop listening for hotkeys."""
        log_debug("Keyboard listener stopping")
        self._stop_enter_listener()
        try:
            keyboard.unhook_all()
        except:
            pass
        self._running = False


# Global listener reference for re-initialization
_listener = None

def create_listener(callback, stt_or_asr):
    """Create and start a keyboard listener."""
    global _listener
    
    if hasattr(stt_or_asr, 'start_recording') and hasattr(stt_or_asr, 'stop_and_transcribe'):
        asr = stt_or_asr
    else:
        from speech.asr import get_engine
        asr = get_engine()

    _listener = KeyboardListener(callback, asr)

    def run():
        _listener.start()
        while _listener._running:
            time.sleep(0.1)

    t = threading.Thread(target=run, daemon=True)
    t.start()

    return _listener

def get_listener():
    """Get current listener for state management."""
    return _listener

def reset_listener():
    """Reset listener state."""
    if _listener:
        _listener.reset_state()
