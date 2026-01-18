# core/main_controller.py
"""
Main controller for AI Desktop Assistant.
Integrates self-healing, voice commands for repair, and automatic problem detection.
"""

# Suppress noisy warnings FIRST
import warnings
import os
from pathlib import Path
from datetime import datetime

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*pkg_resources.*')

import logging
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('huggingface_hub').setLevel(logging.WARNING)
logging.getLogger('faster_whisper').setLevel(logging.WARNING)
logging.getLogger('comtypes').setLevel(logging.WARNING)

import sys
import json
import time
import threading
import re
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Debug logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
DEBUG_LOG = LOG_DIR / "last_session_debug.log"

def log_debug(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [Main] {msg}\n")
    except:
        pass

# Configuration
AUTO_EXECUTE = os.getenv("AUTO_EXECUTE", "true").lower() == "true"
SELF_HEAL_ENABLED = os.getenv("SELF_HEAL_ENABLED", "true").lower() == "true"

# Import components
try:
    from speech.asr import get_engine as get_asr_engine
    ASR_AVAILABLE = True
except ImportError as e:
    ASR_AVAILABLE = False
    get_asr_engine = None
    log_debug(f"ASR import failed: {e}")

try:
    from speech.local_tts import get_tts
    TTS_AVAILABLE = True
except ImportError as e:
    TTS_AVAILABLE = False
    get_tts = None
    log_debug(f"TTS import failed: {e}")

from brain.llm_client import LLMClient
from automation.system_control import SystemControl
from avatar import avatar_ws_client

# Self-healing imports
try:
    from core.watchdog import get_watchdog
    from core.repair_engine import get_repair_engine
    from core.self_heal_planner import get_planner
    from core.approval import get_approval_manager
    from core.self_update import get_updater
    SELF_HEAL_AVAILABLE = True
except ImportError as e:
    SELF_HEAL_AVAILABLE = False
    log_debug(f"Self-heal import failed: {e}")

try:
    from ui.keyboard import create_listener as create_keyboard_listener, get_listener
except ImportError:
    create_keyboard_listener = None
    get_listener = None

try:
    from ui.hud import get_hud
    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False
    get_hud = None

# Self-repair voice command patterns
REPAIR_COMMANDS = {
    "diagnose": ["diagnose", "diagnostic", "status", "health check", "system status"],
    "fix_mic": ["fix mic", "repair mic", "microphone not working", "can't hear me", "fix microphone"],
    "fix_speech": ["fix speech", "repair speech", "fix asr", "transcription not working", "fix recognition"],
    "fix_tts": ["fix tts", "repair tts", "fix voice", "you're not speaking", "can't hear you"],
    "fix_yourself": ["fix yourself", "repair yourself", "self repair", "heal yourself", "auto fix"],
    "fix_hotkeys": ["fix hotkeys", "repair hotkeys", "keys not working", "fix keyboard"],
    "reset_ptt": ["reset ptt", "ptt stuck", "recording stuck", "fix recording"],
    "update": ["update yourself", "self update", "check for updates", "upgrade"],
    "shutdown_autopilot": ["shutdown autopilot", "disable autopilot", "stop autopilot", "kill autopilot", "autopilot off"],
    "approve_pin": ["approve pin", "approve update pin", "confirm pin"],
}


class MainController:
    """Main controller with self-healing capabilities."""

    def __init__(self):
        print("[Main] Initializing AI Desktop Assistant...")
        log_debug("Initialization started")

        # Initialize TTS first
        self.tts = None
        if TTS_AVAILABLE:
            try:
                self.tts = get_tts()
                print("[Main] Local TTS initialized")
            except Exception as e:
                print(f"[Main] TTS init error: {e}")

        # Initialize ASR
        self.asr = None
        if ASR_AVAILABLE:
            try:
                self.asr = get_asr_engine()
                print(f"[Main] ASR initialized: {self.asr.model_name} on {self.asr.device}")
            except Exception as e:
                print(f"[Main] ASR init error: {e}")
                log_debug(f"ASR error: {e}")

        # Other components
        self.llm = LLMClient()
        self.system = SystemControl()
        self.avatar = avatar_ws_client.get_client()
        self.hud = get_hud() if HUD_AVAILABLE else None
        self.keyboard = None

        # Self-healing components
        self.watchdog = None
        self.repair_engine = None
        self.planner = None
        self.approval = None
        self.updater = None

        if SELF_HEAL_ENABLED and SELF_HEAL_AVAILABLE:
            self._init_self_healing()

        # State
        self.running = False
        self._speaking_lock = threading.Lock()

        # Connect avatar
        self._connect_avatar()

        # Start keyboard listener
        if create_keyboard_listener and self.asr:
            try:
                self.keyboard = create_keyboard_listener(self.process_input, self.asr)
                print("[Main] Keyboard listener started")
            except Exception as e:
                print(f"[Main] Keyboard listener failed: {e}")

        log_debug("Initialization complete")

    def _init_self_healing(self):
        """Initialize self-healing subsystem."""
        try:
            self.watchdog = get_watchdog()
            self.repair_engine = get_repair_engine()
            self.planner = get_planner()
            self.approval = get_approval_manager()
            self.updater = get_updater()

            # Set component references
            self.watchdog.set_components(
                asr=self.asr,
                keyboard=get_listener() if get_listener else None,
                tts=self.tts,
                avatar=self.avatar,
                hud=self.hud
            )
            self.repair_engine.set_components(
                asr=self.asr,
                tts=self.tts,
                keyboard=get_listener() if get_listener else None,
                avatar=self.avatar
            )
            self.approval.set_tts(self.tts)
            self.updater.set_tts(self.tts)

            # Set auto-repair callback
            self.watchdog.set_repair_callback(self._on_auto_repair)

            print("[Main] Self-healing system initialized")
            log_debug("Self-healing ready")
        except Exception as e:
            print(f"[Main] Self-healing init error: {e}")
            log_debug(f"Self-healing error: {e}")

    def _on_auto_repair(self, report):
        """Called by watchdog when issues are detected."""
        if not self.planner or not self.repair_engine:
            return

        # Create auto-repair plan
        auto_plan = self.planner.get_auto_plan(report)
        if auto_plan:
            log_debug(f"Auto-repair triggered: {len(auto_plan)} actions")
            self.repair_engine.execute_plan(auto_plan)

    def _speak(self, text: str, block: bool = True):
        """Speak text using TTS."""
        if not text:
            return
        if not self.tts:
            print(f"[TTS] {text}")
            return
        with self._speaking_lock:
            try:
                self.tts.speak(text, block=block)
            except Exception as e:
                log_debug(f"TTS error: {e}")

    def _connect_avatar(self):
        """Connect to VTube Studio avatar."""
        if self.avatar.connect():
            print("[Main] Avatar connected!")
        else:
            print("[Main] Avatar connection failed (optional)")

    def _is_repair_command(self, text: str):
        """Check if text is a self-repair command. Returns (command_type, match) or (None, None)."""
        text_lower = text.lower().strip()
        for cmd_type, patterns in REPAIR_COMMANDS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return cmd_type, pattern
        return None, None

    def _handle_repair_command(self, cmd_type: str, text: str):
        """Handle a self-repair voice command."""
        log_debug(f"Repair command: {cmd_type}")

        if cmd_type == "diagnose":
            self._speak("Running diagnostics.")
            report = self.watchdog.run_diagnostics()
            status_text = self.watchdog.get_status_text()
            self._speak(status_text)
            return True

        elif cmd_type == "fix_mic":
            self._speak("Attempting to fix microphone.")
            results = self.repair_engine.repair_mic_routine()
            return True

        elif cmd_type == "fix_speech":
            self._speak("Fixing speech recognition.")
            self.repair_engine.switch_asr_to_cpu()
            self.repair_engine.restart_asr()
            self._speak("Speech recognition restarted.")
            return True

        elif cmd_type == "fix_tts":
            self._speak("Restarting text to speech.")
            self.repair_engine.restart_tts()
            return True

        elif cmd_type == "fix_yourself":
            self._speak("Running self-repair.")
            report = self.watchdog.run_diagnostics()
            plan = self.planner.get_auto_plan(report)
            if plan:
                summary = self.planner.summarize_plan(self.planner.create_plan(report))
                self._speak(summary)
                results = self.repair_engine.execute_plan(plan)
                successes = sum(1 for r in results if r.result.value == "success")
                self._speak(f"Repair complete. {successes} of {len(results)} actions succeeded.")
            else:
                self._speak("No repairs needed. All systems operational.")
            return True

        elif cmd_type == "fix_hotkeys":
            self._speak("Rebinding hotkeys.")
            self.repair_engine.rebind_hotkeys()
            return True

        elif cmd_type == "reset_ptt":
            self._speak("Resetting PTT state.")
            self.repair_engine.reset_ptt_state()
            return True

        elif cmd_type == "update":
            self._speak("Checking for updates.")
            has_update, summary, files = self.updater.propose_update()
            if has_update:
                self._speak(summary)
                # Request approval
                self.approval.request_approval(
                    "apply software update",
                    summary,
                    on_confirm=lambda: self._run_update(),
                    on_deny=lambda: self._speak("Update cancelled.")
                )
            else:
                self._speak("No updates available.")
            return True

        elif cmd_type == "shutdown_autopilot":
            self._speak("Are you sure you want to disable autopilot? Speak your PIN to confirm.")
            self._pending_autopilot_shutdown = True
            return True

        elif cmd_type == "approve_pin":
            # Handle PIN spoken for pending actions
            if hasattr(self, "_pending_autopilot_shutdown") and self._pending_autopilot_shutdown:
                pin = self._extract_pin(text)
                if pin == os.getenv("APPROVAL_PIN", ""):
                    self._pending_autopilot_shutdown = False
                    self._speak("PIN confirmed. Disabling autopilot.")
                    self._disable_autopilot()
                else:
                    self._speak("Invalid PIN.")
            return True

        return False

    def _run_update(self):
        """Run the update flow after approval."""
        result = self.updater.run_update_flow()
        if result.success:
            self._speak("Update successful. Restarting is recommended.")
        else:
            self._speak(f"Update failed: {result.message}")

    def _extract_pin(self, text: str) -> str:
        """Extract PIN digits from spoken text like 'approve pin 1 2 3 4'."""
        import re
        # Find all digits in the text
        digits = re.findall(r"\d", text)
        return "".join(digits)

    def _disable_autopilot(self):
        """Disable autopilot by running the kill-switch."""
        import subprocess
        try:
            # Update .env
            env_path = Path(__file__).parent.parent / ".env"
            content = env_path.read_text()
            content = content.replace("SELF_HEAL_AUTO_REPAIR=true", "SELF_HEAL_AUTO_REPAIR=false")
            content = content.replace("SELF_UPDATE_AUTO_APPLY=true", "SELF_UPDATE_AUTO_APPLY=false")
            env_path.write_text(content)
            
            # Log the action
            log_file = Path(__file__).parent.parent / "logs" / "autopilot_actions.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] AUTOPILOT DISABLED by voice command\n")
            
            self._speak("Autopilot has been disabled. Auto-repair and auto-update are now off.")
            log_debug("Autopilot disabled by voice command")
        except Exception as e:
            self._speak(f"Failed to disable autopilot: {e}")
            log_debug(f"Autopilot disable error: {e}")

    def process_input(self, text: str):
        """Process user input (voice or typed)."""
        if not text or not text.strip():
            self._speak("I didn't catch that.")
            return

        text = text.strip()
        print(f"\n[You]: {text}")
        log_debug(f"Input: {text}")

        # Check for pending approval first
        if self.approval and self.approval.is_pending():
            handled, result = self.approval.check_response(text)
            if handled:
                return

        # Check for repair commands
        cmd_type, match = self._is_repair_command(text)
        if cmd_type and self.watchdog:
            self._handle_repair_command(cmd_type, text)
            return

        # Quick commands
        if self._try_quick_command(text):
            return

        # Send to LLM
        try:
            self._speak("Let me think.", block=False)
            response = self.llm.get_response(text)
            print(f"[AI]: {response[:200]}...")
            self._process_response(response)
        except Exception as e:
            print(f"[Error] LLM: {e}")
            self._speak("Sorry, I had trouble processing that.")

    def _try_quick_command(self, text: str) -> bool:
        """Try quick command patterns."""
        text_lower = text.lower()

        # Open app
        match = re.search(r'open\s+(youtube|notepad|calculator|chrome|spotify|discord|vscode)', text_lower)
        if match:
            app = match.group(1)
            self._speak(f"Opening {app}.")
            self.system.open_app(app)
            return True

        # Search
        match = re.search(r'search\s+(.+)', text_lower)
        if match:
            query = match.group(1)
            self._speak(f"Searching for {query}.")
            self.system.search_google(query)
            return True

        # Volume
        match = re.search(r'volume\s+(up|down|mute)', text_lower)
        if match:
            direction = match.group(1)
            self._speak(f"Volume {direction}.")
            self.system.adjust_volume(direction)
            return True

        return False

    def _process_response(self, response: str):
        """Process LLM response."""
        try:
            json_match = re.search(r'\{[^{}]+\}', response)
            if json_match:
                action = json.loads(json_match.group())
                self._handle_action(action, response)
                return
        except:
            pass
        # Default: speak
        self._speak(response)

    def _handle_action(self, action: dict, full_response: str):
        """Handle action from LLM."""
        act = action.get('action', '').upper()
        params = action.get('params', {})

        if act == 'OPEN_APP':
            app = params.get('app', params.get('name', ''))
            self._speak(f"Opening {app}.")
            self.system.open_app(app)
        elif act == 'SEARCH':
            query = params.get('query', '')
            self._speak(f"Searching {query}.")
            self.system.search_google(query)
        elif act == 'SPEAK':
            self._speak(params.get('text', full_response))
        else:
            self._speak(params.get('text', full_response))

    def run(self):
        """Main run loop."""
        print("\n" + "=" * 50)
        print("AI Desktop Assistant Started!")
        print("=" * 50)
        print("CONTROLS:")
        print("  Ctrl+Alt+Space : Start/stop recording")
        print("  Ctrl+Alt+T     : Type a command")
        print("=" * 50)
        print("REPAIR COMMANDS (voice or text):")
        print("  'diagnose' - Run diagnostics")
        print("  'fix yourself' - Auto-repair")
        print("  'fix microphone' - Repair mic/ASR")
        print("  'update yourself' - Check for updates")
        print("=" * 50)

        self.running = True

        # Start watchdog (don't auto-repair immediately, let it warm up)
        if self.watchdog and SELF_HEAL_ENABLED:
            threading.Timer(10.0, self.watchdog.start).start()

        self._speak("Hello! I'm ready. Say 'diagnose' for system status or 'fix yourself' if something's wrong.")

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[Main] Stopping...")

        self.stop()

    def stop(self):
        """Stop the assistant."""
        self.running = False
        if self.watchdog:
            self.watchdog.stop()
        if self.asr:
            self.asr.stop_stream()
        if self.avatar:
            self.avatar.close()
        print("[Main] Goodbye!")


def main():
    controller = MainController()
    controller.run()


if __name__ == '__main__':
    main()
