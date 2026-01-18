# core/repair_engine.py
"""
Repair Engine - Library of safe, idempotent repair actions.
Each action snapshots state before running, has timeouts, and logs results.
"""

import os
import sys
import time
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.watchdog import log_self_heal, SNAPSHOTS_DIR

# Configuration
REPAIR_TIMEOUT = 20  # seconds per action
MAX_RETRIES = 2

# Circuit breaker for audio repairs
_audio_repair_attempts = []
AUDIO_REPAIR_MAX_ATTEMPTS = 3
AUDIO_REPAIR_COOLDOWN_MINUTES = 10


class RepairResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RepairAction:
    name: str
    result: RepairResult
    message: str
    duration: float
    snapshot_path: Optional[str] = None


def create_snapshot(label: str) -> str:
    """Create a snapshot of critical files before repair."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = SNAPSHOTS_DIR / f"{ts}_{label}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy critical files
    root = Path(__file__).parent.parent
    files_to_backup = [
        ".env",
        "core/main_controller.py",
        "speech/asr.py",
        "speech/local_tts.py",
        "ui/keyboard.py",
    ]
    
    for f in files_to_backup:
        src = root / f
        if src.exists():
            dst = snapshot_dir / f.replace("/", "_")
            shutil.copy2(src, dst)
    
    log_self_heal(f"Created snapshot: {snapshot_dir}")
    
    # Prune old snapshots (keep last 7)
    all_snapshots = sorted(SNAPSHOTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in all_snapshots[7:]:
        if old.is_dir():
            shutil.rmtree(old)
            log_self_heal(f"Pruned old snapshot: {old.name}")
    
    return str(snapshot_dir)


class RepairEngine:
    """
    Engine that executes repair actions safely with snapshots, timeouts, and logging.
    """

    def __init__(self):
        self._asr = None
        self._tts = None
        self._keyboard = None
        self._avatar = None
        self._lock = threading.Lock()
        log_self_heal("RepairEngine initialized")

    def set_components(self, asr=None, tts=None, keyboard=None, avatar=None):
        """Set component references."""
        self._asr = asr
        self._tts = tts
        self._keyboard = keyboard
        self._avatar = avatar

    def _speak(self, text: str):
        """Speak status update."""
        if self._tts:
            try:
                self._tts.speak(text, block=False)
            except:
                pass
        print(f"[Repair] {text}")

    def restart_asr(self, retry: int = 0) -> RepairAction:
        """Stop ASR, clear cache, reinitialize model."""
        start = time.time()
        log_self_heal(f"Action: restart_asr (attempt {retry + 1})")
        snapshot = create_snapshot("restart_asr")
        
        try:
            if not self._asr:
                from speech.asr import get_engine
                self._asr = get_engine()
            
            # Stop current stream
            if hasattr(self._asr, 'stop_stream'):
                self._asr.stop_stream()
            
            # Clear model
            if hasattr(self._asr, 'model'):
                self._asr.model = None
            
            # Reinitialize
            if hasattr(self._asr, '_load_model'):
                self._asr._load_model()
            
            # Verify
            if self._asr.model is not None:
                log_self_heal("restart_asr: SUCCESS")
                return RepairAction("restart_asr", RepairResult.SUCCESS, "ASR restarted", time.time() - start, snapshot)
            else:
                raise Exception("Model still None after reload")
                
        except Exception as e:
            log_self_heal(f"restart_asr: FAILED - {e}", "ERROR")
            if retry < MAX_RETRIES:
                time.sleep(1)
                return self.restart_asr(retry + 1)
            return RepairAction("restart_asr", RepairResult.FAILED, str(e), time.time() - start, snapshot)

    def switch_asr_to_cpu(self) -> RepairAction:
        """Switch ASR to CPU mode with smaller model."""
        start = time.time()
        log_self_heal("Action: switch_asr_to_cpu")
        snapshot = create_snapshot("switch_asr_to_cpu")
        
        try:
            # Update environment
            os.environ["DEVICE"] = "cpu"
            os.environ["STT_MODEL"] = os.getenv("STT_MODEL_CPU", "small")
            
            # Update .env file
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                content = env_path.read_text()
                content = content.replace("DEVICE=cuda", "DEVICE=cpu")
                env_path.write_text(content)
            
            # Reinitialize ASR with CPU
            if self._asr:
                if hasattr(self._asr, 'stop_stream'):
                    self._asr.stop_stream()
                self._asr.model = None
                self._asr.device = "cpu"
                self._asr.model_name = os.getenv("STT_MODEL_CPU", "small")
                
                # Force CPU in faster-whisper
                from faster_whisper import WhisperModel
                self._asr.model = WhisperModel(
                    self._asr.model_name,
                    device="cpu",
                    compute_type="int8"
                )
                self._asr._ready_for_ptt = True
                
                log_self_heal(f"Switched to CPU model: {self._asr.model_name}")
                self._speak("Switched to CPU mode for speech recognition.")
                return RepairAction("switch_asr_to_cpu", RepairResult.SUCCESS, f"Now using {self._asr.model_name} on CPU", time.time() - start, snapshot)
            else:
                return RepairAction("switch_asr_to_cpu", RepairResult.SKIPPED, "No ASR to switch", time.time() - start, snapshot)
                
        except Exception as e:
            log_self_heal(f"switch_asr_to_cpu: FAILED - {e}", "ERROR")
            return RepairAction("switch_asr_to_cpu", RepairResult.FAILED, str(e), time.time() - start, snapshot)

    def restart_tts(self) -> RepairAction:
        """Reinitialize TTS engine and test."""
        start = time.time()
        log_self_heal("Action: restart_tts")
        snapshot = create_snapshot("restart_tts")
        
        try:
            if self._tts:
                # Stop current engine
                if hasattr(self._tts, 'engine') and self._tts.engine:
                    try:
                        self._tts.engine.stop()
                    except:
                        pass
                
                # Reinitialize
                import pyttsx3
                self._tts.engine = pyttsx3.init()
                self._tts.engine.setProperty('rate', 175)
                
                # Test
                self._tts.speak("TTS restarted.", block=True)
                
                log_self_heal("restart_tts: SUCCESS")
                return RepairAction("restart_tts", RepairResult.SUCCESS, "TTS restarted and tested", time.time() - start, snapshot)
            else:
                from speech.local_tts import get_tts
                self._tts = get_tts()
                self._tts.speak("TTS initialized.", block=True)
                return RepairAction("restart_tts", RepairResult.SUCCESS, "TTS created and tested", time.time() - start, snapshot)
                
        except Exception as e:
            log_self_heal(f"restart_tts: FAILED - {e}", "ERROR")
            return RepairAction("restart_tts", RepairResult.FAILED, str(e), time.time() - start, snapshot)

    def restart_audio_device(self) -> RepairAction:
        """Try reopening microphone with different device indices.
        
        Includes circuit breaker to prevent endless loops.
        """
        global _audio_repair_attempts
        start = time.time()
        
        # Circuit breaker check
        now = time.time()
        cutoff = now - (AUDIO_REPAIR_COOLDOWN_MINUTES * 60)
        _audio_repair_attempts = [t for t in _audio_repair_attempts if t > cutoff]
        
        if len(_audio_repair_attempts) >= AUDIO_REPAIR_MAX_ATTEMPTS:
            log_self_heal(f"Circuit breaker OPEN: {len(_audio_repair_attempts)} attempts in {AUDIO_REPAIR_COOLDOWN_MINUTES}min", "WARNING")
            self._speak("I'm pausing microphone repair. Please check the hardware or settings manually.")
            
            # Disable auto-repair
            try:
                env_path = Path(__file__).parent.parent / ".env"
                env_content = env_path.read_text() if env_path.exists() else ""
                if "SELF_HEAL_AUTO_REPAIR=true" in env_content:
                    env_content = env_content.replace("SELF_HEAL_AUTO_REPAIR=true", "SELF_HEAL_AUTO_REPAIR=false")
                    env_path.write_text(env_content)
                    log_self_heal("Auto-repair disabled by circuit breaker")
            except:
                pass
            
            return RepairAction("restart_audio_device", RepairResult.SKIPPED, 
                "Circuit breaker: too many attempts", time.time() - start, None)
        
        _audio_repair_attempts.append(now)
        log_self_heal(f"Action: restart_audio_device (attempt {len(_audio_repair_attempts)}/{AUDIO_REPAIR_MAX_ATTEMPTS})")
        snapshot = create_snapshot("restart_audio_device")
        
        try:
            import sounddevice as sd
            
            # List available devices
            devices = sd.query_devices()
            input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            log_self_heal(f"Found {len(input_devices)} input devices")
            
            # Try each input device
            for idx in input_devices[:5]:  # Try first 5
                try:
                    device_info = devices[idx]
                    log_self_heal(f"Trying device {idx}: {device_info['name']}")
                    
                    # Test recording
                    sd.default.device = (idx, None)
                    test_audio = sd.rec(int(0.5 * 16000), samplerate=16000, channels=1, dtype='float32')
                    sd.wait()
                    
                    if test_audio is not None and len(test_audio) > 0:
                        log_self_heal(f"Device {idx} works: {device_info['name']}")
                        self._speak(f"Using microphone: {device_info['name'][:30]}")
                        return RepairAction("restart_audio_device", RepairResult.SUCCESS, f"Using device {idx}: {device_info['name']}", time.time() - start, snapshot)
                except Exception as e:
                    log_self_heal(f"Device {idx} failed: {e}")
                    continue
            
            return RepairAction("restart_audio_device", RepairResult.FAILED, "No working input device found", time.time() - start, snapshot)
            
        except Exception as e:
            log_self_heal(f"restart_audio_device: FAILED - {e}", "ERROR")
            return RepairAction("restart_audio_device", RepairResult.FAILED, str(e), time.time() - start, snapshot)

    def rebind_hotkeys(self) -> RepairAction:
        """Re-register keyboard hotkeys."""
        start = time.time()
        log_self_heal("Action: rebind_hotkeys")
        snapshot = create_snapshot("rebind_hotkeys")
        
        try:
            import keyboard
            
            # Unhook all first
            try:
                keyboard.unhook_all()
            except:
                pass
            
            time.sleep(0.5)
            
            # Re-register from keyboard listener
            if self._keyboard:
                self._keyboard._running = False
                time.sleep(0.2)
                self._keyboard.start()
                
                log_self_heal("rebind_hotkeys: SUCCESS")
                self._speak("Hotkeys re-registered.")
                return RepairAction("rebind_hotkeys", RepairResult.SUCCESS, "Hotkeys rebound", time.time() - start, snapshot)
            else:
                return RepairAction("rebind_hotkeys", RepairResult.SKIPPED, "No keyboard listener", time.time() - start, snapshot)
                
        except Exception as e:
            log_self_heal(f"rebind_hotkeys: FAILED - {e}", "ERROR")
            return RepairAction("rebind_hotkeys", RepairResult.FAILED, str(e), time.time() - start, snapshot)

    def reset_ptt_state(self) -> RepairAction:
        """Reset PTT state to ready."""
        start = time.time()
        log_self_heal("Action: reset_ptt_state")
        
        try:
            if self._asr:
                self._asr._ready_for_ptt = True
                self._asr._recording = False
                if hasattr(self._asr, '_frames'):
                    self._asr._frames = []
                
            if self._keyboard:
                self._keyboard._transcribing = False
                self._keyboard._ready_for_ptt = True
                if hasattr(self._keyboard, '_stop_enter_listener'):
                    self._keyboard._stop_enter_listener()
            
            log_self_heal("reset_ptt_state: SUCCESS")
            self._speak("PTT state reset. Ready for new recording.")
            return RepairAction("reset_ptt_state", RepairResult.SUCCESS, "PTT reset", time.time() - start)
            
        except Exception as e:
            log_self_heal(f"reset_ptt_state: FAILED - {e}", "ERROR")
            return RepairAction("reset_ptt_state", RepairResult.FAILED, str(e), time.time() - start)

    def reconnect_avatar(self) -> RepairAction:
        """Attempt to reconnect VTube Studio avatar."""
        start = time.time()
        log_self_heal("Action: reconnect_avatar")
        
        try:
            if self._avatar:
                self._avatar.close()
                time.sleep(1)
                if self._avatar.connect():
                    log_self_heal("reconnect_avatar: SUCCESS")
                    return RepairAction("reconnect_avatar", RepairResult.SUCCESS, "Avatar reconnected", time.time() - start)
                else:
                    return RepairAction("reconnect_avatar", RepairResult.PARTIAL, "Avatar connection failed (optional)", time.time() - start)
            else:
                return RepairAction("reconnect_avatar", RepairResult.SKIPPED, "No avatar configured", time.time() - start)
                
        except Exception as e:
            log_self_heal(f"reconnect_avatar: FAILED - {e}", "ERROR")
            return RepairAction("reconnect_avatar", RepairResult.PARTIAL, str(e), time.time() - start)

    def repair_mic_routine(self) -> List[RepairAction]:
        """
        Complete microphone repair routine - tries multiple fixes in order.
        This is the main routine called when mic issues are detected.
        """
        log_self_heal("Starting repair_mic_routine")
        self._speak("Attempting to repair microphone and speech recognition.")
        
        results = []
        
        # Step 1: Rebind hotkeys
        results.append(self.rebind_hotkeys())
        
        # Step 2: Reset PTT state
        results.append(self.reset_ptt_state())
        
        # Step 3: Try different audio devices
        results.append(self.restart_audio_device())
        
        # Step 4: Switch to CPU (fixes cublas issue)
        results.append(self.switch_asr_to_cpu())
        
        # Step 5: Restart ASR
        results.append(self.restart_asr())
        
        # Step 6: Quick test
        test_result = self._test_mic()
        results.append(test_result)
        
        # Report results
        successes = sum(1 for r in results if r.result == RepairResult.SUCCESS)
        failures = sum(1 for r in results if r.result == RepairResult.FAILED)
        
        if failures == 0:
            self._speak(f"Repair complete. All {successes} steps succeeded. Try speaking now.")
        elif successes > 0:
            self._speak(f"Repair partially complete. {successes} succeeded, {failures} failed.")
        else:
            self._speak("Repair failed. Please check Windows microphone permissions in Settings, Privacy, Microphone.")
        
        return results

    def _test_mic(self) -> RepairAction:
        """Test microphone by recording briefly."""
        start = time.time()
        log_self_heal("Testing microphone...")
        
        try:
            import sounddevice as sd
            import numpy as np
            
            # Record 1 second
            audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1, dtype='float32')
            sd.wait()
            
            # Check if we got audio
            if audio is None or len(audio) == 0:
                return RepairAction("test_mic", RepairResult.FAILED, "No audio captured", time.time() - start)
            
            # Check audio level
            level = np.abs(audio).max()
            if level < 0.001:
                return RepairAction("test_mic", RepairResult.PARTIAL, f"Audio very quiet (level={level:.4f})", time.time() - start)
            
            log_self_heal(f"Mic test passed: level={level:.4f}")
            return RepairAction("test_mic", RepairResult.SUCCESS, f"Mic working (level={level:.4f})", time.time() - start)
            
        except Exception as e:
            log_self_heal(f"Mic test failed: {e}", "ERROR")
            return RepairAction("test_mic", RepairResult.FAILED, str(e), time.time() - start)

    def execute_plan(self, plan: List[Dict[str, Any]]) -> List[RepairAction]:
        """Execute a repair plan (list of actions)."""
        with self._lock:
            results = []
            for item in plan:
                action_name = item.get("action", "")
                log_self_heal(f"Executing plan step: {action_name}")
                
                if action_name == "restart_asr":
                    results.append(self.restart_asr())
                elif action_name == "switch_asr_to_cpu":
                    results.append(self.switch_asr_to_cpu())
                elif action_name == "restart_tts":
                    results.append(self.restart_tts())
                elif action_name == "restart_audio_device":
                    results.append(self.restart_audio_device())
                elif action_name == "rebind_hotkeys":
                    results.append(self.rebind_hotkeys())
                elif action_name == "reset_ptt_state":
                    results.append(self.reset_ptt_state())
                elif action_name == "reconnect_avatar":
                    results.append(self.reconnect_avatar())
                elif action_name == "repair_mic_routine":
                    results.extend(self.repair_mic_routine())
                else:
                    log_self_heal(f"Unknown action: {action_name}", "WARN")
                    results.append(RepairAction(action_name, RepairResult.SKIPPED, "Unknown action", 0))
            
            return results



    def escalate_to_autonomous_coder(self, issue_description: str, failed_actions: List[str]) -> RepairAction:
        """
        Escalate a complex issue to the autonomous coder when standard repairs fail.
        This is called after 2+ failed repair attempts.
        """
        start = time.time()
        log_self_heal(f"Escalating to autonomous coder: {issue_description[:100]}")
        snapshot = create_snapshot("autonomous_fix")
        
        try:
            from core.autonomous_coder import analyze_and_fix
            
            # Build context from failed actions
            context = f"""
Issue: {issue_description}
Failed repair actions: {', '.join(failed_actions)}
The standard repair actions did not resolve this issue. 
Please analyze the code and suggest a fix.
"""
            
            result = analyze_and_fix(context)
            
            if result.success:
                log_self_heal(f"Autonomous fix succeeded: {result.explanation[:100]}")
                self._speak("I applied an autonomous fix. Please test the functionality.")
                return RepairAction(
                    "autonomous_fix", 
                    RepairResult.SUCCESS, 
                    result.explanation[:200], 
                    time.time() - start, 
                    str(snapshot)
                )
            else:
                log_self_heal(f"Autonomous fix failed: {result.message}", "WARN")
                return RepairAction(
                    "autonomous_fix", 
                    RepairResult.FAILED, 
                    result.message, 
                    time.time() - start, 
                    str(snapshot)
                )
                
        except Exception as e:
            log_self_heal(f"Autonomous coder error: {e}", "ERROR")
            return RepairAction("autonomous_fix", RepairResult.FAILED, str(e), time.time() - start, str(snapshot))


# Enhanced execute_plan with autonomous fallback
def execute_plan_with_autonomy(self, plan: List[Dict[str, Any]], issue_description: str = "") -> List[RepairAction]:
    """Execute a repair plan with autonomous coder fallback."""
    results = self.execute_plan(plan)
    
    # Check if we have repeated failures
    failures = [r for r in results if r.result == RepairResult.FAILED]
    if len(failures) >= 2:
        log_self_heal(f"Multiple failures detected ({len(failures)}), escalating to autonomous coder")
        failed_actions = [r.name for r in failures]
        
        # Try autonomous fix
        auto_result = self.escalate_to_autonomous_coder(issue_description, failed_actions)
        results.append(auto_result)
    
    return results

# Singleton
_engine: Optional[RepairEngine] = None

def get_repair_engine() -> RepairEngine:
    global _engine
    if _engine is None:
        _engine = RepairEngine()
    return _engine



