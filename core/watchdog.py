# core/watchdog.py
"""
Watchdog & Diagnostics Service - Continuously monitors health and performs rapid recovery.
Polls components every 2-5s and triggers automatic repairs when problems are detected.
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
SELF_HEAL_LOG = LOG_DIR / "self_heal.log"
SNAPSHOTS_DIR = LOG_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    last_check: float
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosticReport:
    timestamp: float
    components: Dict[str, ComponentHealth]
    overall_status: HealthStatus
    issues: List[str]
    recommendations: List[str]


def log_self_heal(msg: str, level: str = "INFO"):
    """Log to self_heal.log"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(SELF_HEAL_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(f"[Watchdog] {msg}")


class Watchdog:
    """
    Health monitoring service that continuously watches all components
    and triggers automatic repairs when problems are detected.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_interval = 3.0  # seconds
        self._components: Dict[str, ComponentHealth] = {}
        self._last_diagnostics: Optional[DiagnosticReport] = None
        self._repair_callback: Optional[Callable] = None
        self._tts = None
        self._hud = None
        
        # Component references (set by main_controller)
        self._asr = None
        self._keyboard = None
        self._avatar = None
        
        # Health metrics
        self._last_mic_frame_time = 0
        self._last_transcription_time = 0
        self._last_tts_success_time = 0
        self._transcription_latencies: List[float] = []
        
        log_self_heal("Watchdog initialized")

    def set_components(self, asr=None, keyboard=None, tts=None, avatar=None, hud=None):
        """Set references to monitored components."""
        self._asr = asr
        self._keyboard = keyboard
        self._tts = tts
        self._avatar = avatar
        self._hud = hud
        log_self_heal(f"Components registered: ASR={asr is not None}, Keyboard={keyboard is not None}, TTS={tts is not None}")

    def set_repair_callback(self, callback: Callable):
        """Set callback to invoke repair engine."""
        self._repair_callback = callback

    def record_mic_frame(self):
        """Called when audio frame is received."""
        self._last_mic_frame_time = time.time()

    def record_transcription(self, latency: float):
        """Called after successful transcription."""
        self._last_transcription_time = time.time()
        self._transcription_latencies.append(latency)
        if len(self._transcription_latencies) > 10:
            self._transcription_latencies.pop(0)

    def record_tts_success(self):
        """Called after TTS playback completes."""
        self._last_tts_success_time = time.time()

    def _check_mic_alive(self) -> ComponentHealth:
        """Check if microphone is receiving audio frames."""
        now = time.time()
        
        # Only check if we're supposed to be recording
        if self._asr and hasattr(self._asr, '_recording') and self._asr._recording:
            time_since_frame = now - self._last_mic_frame_time if self._last_mic_frame_time else float('inf')
            if time_since_frame > 2.0:
                return ComponentHealth(
                    name="microphone",
                    status=HealthStatus.FAILED,
                    last_check=now,
                    message=f"No audio frames for {time_since_frame:.1f}s while recording",
                    metrics={"last_frame_age": time_since_frame}
                )
        
        return ComponentHealth(
            name="microphone",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message="Microphone OK",
            metrics={"last_frame_time": self._last_mic_frame_time}
        )

    def _check_asr_ready(self) -> ComponentHealth:
        """Check ASR model status."""
        now = time.time()
        
        if not self._asr:
            return ComponentHealth(
                name="asr",
                status=HealthStatus.UNKNOWN,
                last_check=now,
                message="ASR not initialized"
            )
        
        # Check if model is loaded
        model_loaded = hasattr(self._asr, 'model') and self._asr.model is not None
        if not model_loaded:
            return ComponentHealth(
                name="asr",
                status=HealthStatus.FAILED,
                last_check=now,
                message="ASR model not loaded"
            )
        
        # Check for CUDA errors (cublas missing)
        if hasattr(self._asr, '_last_error') and 'cublas' in str(self._asr._last_error).lower():
            return ComponentHealth(
                name="asr",
                status=HealthStatus.DEGRADED,
                last_check=now,
                message="CUDA cublas library missing - need CPU fallback",
                metrics={"error": str(self._asr._last_error)}
            )
        
        # Check average latency
        avg_latency = sum(self._transcription_latencies) / len(self._transcription_latencies) if self._transcription_latencies else 0
        if avg_latency > 10.0:
            return ComponentHealth(
                name="asr",
                status=HealthStatus.DEGRADED,
                last_check=now,
                message=f"High transcription latency: {avg_latency:.1f}s",
                metrics={"avg_latency": avg_latency}
            )
        
        return ComponentHealth(
            name="asr",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message=f"ASR ready ({self._asr.model_name} on {self._asr.device})",
            metrics={"model": self._asr.model_name, "device": self._asr.device, "avg_latency": avg_latency}
        )

    def _check_tts_ready(self) -> ComponentHealth:
        """Check TTS engine status."""
        now = time.time()
        
        if not self._tts:
            return ComponentHealth(
                name="tts",
                status=HealthStatus.UNKNOWN,
                last_check=now,
                message="TTS not initialized"
            )
        
        # Check if engine is available
        engine_ok = hasattr(self._tts, 'engine') and self._tts.engine is not None
        if not engine_ok:
            return ComponentHealth(
                name="tts",
                status=HealthStatus.FAILED,
                last_check=now,
                message="TTS engine not available"
            )
        
        # Check for recent playback issues (0.1s is suspiciously fast)
        if hasattr(self._tts, '_last_duration') and self._tts._last_duration < 0.5:
            return ComponentHealth(
                name="tts",
                status=HealthStatus.DEGRADED,
                last_check=now,
                message="TTS playback too fast - audio may not be playing",
                metrics={"last_duration": self._tts._last_duration}
            )
        
        return ComponentHealth(
            name="tts",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message="TTS ready",
            metrics={"last_success": self._last_tts_success_time}
        )

    def _check_hotkeys_registered(self) -> ComponentHealth:
        """Check if keyboard hotkeys are registered."""
        now = time.time()
        
        if not self._keyboard:
            return ComponentHealth(
                name="hotkeys",
                status=HealthStatus.UNKNOWN,
                last_check=now,
                message="Keyboard listener not initialized"
            )
        
        running = hasattr(self._keyboard, '_running') and self._keyboard._running
        if not running:
            return ComponentHealth(
                name="hotkeys",
                status=HealthStatus.FAILED,
                last_check=now,
                message="Keyboard listener not running"
            )
        
        return ComponentHealth(
            name="hotkeys",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message="Hotkeys registered"
        )

    def _check_avatar_connected(self) -> ComponentHealth:
        """Check avatar WebSocket connection."""
        now = time.time()
        
        if not self._avatar:
            return ComponentHealth(
                name="avatar",
                status=HealthStatus.UNKNOWN,
                last_check=now,
                message="Avatar not initialized"
            )
        
        connected = hasattr(self._avatar, 'ws') and self._avatar.ws is not None
        if not connected:
            return ComponentHealth(
                name="avatar",
                status=HealthStatus.DEGRADED,  # Not critical
                last_check=now,
                message="Avatar not connected (optional)"
            )
        
        return ComponentHealth(
            name="avatar",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message="Avatar connected"
        )

    def _check_ptt_ready(self) -> ComponentHealth:
        """Check PTT lifecycle state."""
        now = time.time()
        
        if not self._asr:
            return ComponentHealth(
                name="ptt",
                status=HealthStatus.UNKNOWN,
                last_check=now,
                message="ASR not initialized"
            )
        
        ready = hasattr(self._asr, '_ready_for_ptt') and self._asr._ready_for_ptt
        recording = hasattr(self._asr, '_recording') and self._asr._recording
        
        if not ready and not recording:
            return ComponentHealth(
                name="ptt",
                status=HealthStatus.DEGRADED,
                last_check=now,
                message="PTT not ready and not recording - may be stuck"
            )
        
        return ComponentHealth(
            name="ptt",
            status=HealthStatus.HEALTHY,
            last_check=now,
            message="PTT ready" if ready else "PTT recording",
            metrics={"ready": ready, "recording": recording}
        )

    def run_diagnostics(self) -> DiagnosticReport:
        """Run full diagnostic check on all components."""
        log_self_heal("Running diagnostics...")
        now = time.time()
        
        # Check all components
        checks = [
            self._check_mic_alive(),
            self._check_asr_ready(),
            self._check_tts_ready(),
            self._check_hotkeys_registered(),
            self._check_avatar_connected(),
            self._check_ptt_ready(),
        ]
        
        components = {c.name: c for c in checks}
        
        # Determine overall status
        statuses = [c.status for c in checks]
        if HealthStatus.FAILED in statuses:
            overall = HealthStatus.FAILED
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        for c in checks:
            if c.status == HealthStatus.FAILED:
                issues.append(f"{c.name}: {c.message}")
                if c.name == "asr":
                    recommendations.append("restart_asr")
                    if "cublas" in c.message.lower():
                        recommendations.append("switch_asr_to_cpu")
                elif c.name == "microphone":
                    recommendations.append("restart_audio_device")
                elif c.name == "tts":
                    recommendations.append("restart_tts")
                elif c.name == "hotkeys":
                    recommendations.append("rebind_hotkeys")
                elif c.name == "ptt":
                    recommendations.append("reset_ptt_state")
            elif c.status == HealthStatus.DEGRADED:
                issues.append(f"{c.name}: {c.message}")
                if "cublas" in c.message.lower():
                    recommendations.append("switch_asr_to_cpu")
                if "too fast" in c.message.lower():
                    recommendations.append("restart_tts")
        
        report = DiagnosticReport(
            timestamp=now,
            components=components,
            overall_status=overall,
            issues=issues,
            recommendations=list(dict.fromkeys(recommendations))  # Remove duplicates
        )
        
        self._last_diagnostics = report
        
        # Log
        status_str = overall.value.upper()
        log_self_heal(f"Diagnostics complete: {status_str}, {len(issues)} issues, {len(recommendations)} recommendations")
        for issue in issues:
            log_self_heal(f"  Issue: {issue}")
        
        return report

    def get_status(self) -> Dict[str, Any]:
        """Get current status summary."""
        if not self._last_diagnostics:
            self.run_diagnostics()
        
        d = self._last_diagnostics
        return {
            "overall": d.overall_status.value,
            "issues": d.issues,
            "recommendations": d.recommendations,
            "last_check": d.timestamp,
            "components": {name: c.status.value for name, c in d.components.items()}
        }

    def get_status_text(self) -> str:
        """Get human-readable status for TTS."""
        status = self.get_status()
        
        if status["overall"] == "healthy":
            return "All systems operational."
        
        issue_count = len(status["issues"])
        if issue_count == 1:
            return f"I detected one issue: {status['issues'][0]}"
        else:
            return f"I detected {issue_count} issues. Main problem: {status['issues'][0]}"

    def _poll_loop(self):
        """Background polling loop."""
        while self._running:
            try:
                report = self.run_diagnostics()
                
                # Auto-trigger repairs if enabled
                if report.overall_status in [HealthStatus.FAILED, HealthStatus.DEGRADED]:
                    if self._repair_callback and os.getenv("SELF_HEAL_AUTO_REPAIR", "true").lower() == "true":
                        log_self_heal("Auto-triggering repair due to detected issues")
                        try:
                            self._repair_callback(report)
                        except Exception as e:
                            log_self_heal(f"Repair callback error: {e}", "ERROR")
                
            except Exception as e:
                log_self_heal(f"Poll error: {e}", "ERROR")
            
            time.sleep(self._poll_interval)

    def start(self):
        """Start background monitoring."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        log_self_heal("Watchdog monitoring started")

    def stop(self):
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        log_self_heal("Watchdog monitoring stopped")


# Singleton
_watchdog: Optional[Watchdog] = None

def get_watchdog() -> Watchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = Watchdog()
    return _watchdog
