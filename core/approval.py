# core/approval.py
"""
Approval Protocol - Handles user confirmation for dangerous actions.
Supports voice and text approval with security tokens.
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.watchdog import log_self_heal

# Configuration
APPROVAL_TIMEOUT = 15.0  # seconds
APPROVAL_PIN = os.getenv("APPROVAL_PIN", "")  # Optional 4-digit code


@dataclass
class ApprovalRequest:
    action: str
    reason: str
    timestamp: float
    expires: float
    requires_pin: bool = False


class ApprovalManager:
    """
    Manages user approval for dangerous actions.
    Supports voice confirmation, text confirmation, and optional PIN.
    """

    # Positive confirmation phrases
    CONFIRM_PHRASES = [
        "yes", "y", "yeah", "yep", "yup",
        "approve", "approved", "confirm", "confirmed",
        "do it", "go ahead", "proceed", "ok", "okay",
        "sure", "affirmative", "allow", "accept"
    ]

    # Negative confirmation phrases
    DENY_PHRASES = [
        "no", "n", "nope", "nah",
        "cancel", "abort", "stop", "deny", "denied",
        "don't", "dont", "nevermind", "reject"
    ]

    def __init__(self):
        self._pending: Optional[ApprovalRequest] = None
        self._tts = None
        self._callback_on_confirm: Optional[Callable] = None
        self._callback_on_deny: Optional[Callable] = None
        self._timer: Optional[threading.Timer] = None
        self._approval_log: list = []
        log_self_heal("ApprovalManager initialized")

    def set_tts(self, tts):
        """Set TTS for speaking prompts."""
        self._tts = tts

    def _speak(self, text: str):
        """Speak approval prompt."""
        if self._tts:
            try:
                self._tts.speak(text, block=False)
            except:
                pass
        print(f"[Approval] {text}")

    def request_approval(
        self,
        action: str,
        reason: str,
        on_confirm: Optional[Callable] = None,
        on_deny: Optional[Callable] = None,
        requires_pin: bool = False
    ) -> bool:
        """
        Request user approval for an action.
        Returns True if request was created, False if one is already pending.
        """
        if self._pending:
            log_self_heal(f"Approval already pending for {self._pending.action}")
            return False

        # Cancel any existing timer
        self._cancel_timer()

        now = time.time()
        self._pending = ApprovalRequest(
            action=action,
            reason=reason,
            timestamp=now,
            expires=now + APPROVAL_TIMEOUT,
            requires_pin=requires_pin or bool(APPROVAL_PIN)
        )
        self._callback_on_confirm = on_confirm
        self._callback_on_deny = on_deny

        # Speak the prompt
        if requires_pin and APPROVAL_PIN:
            self._speak(f"I need your approval to {action}. Say 'approve' followed by your PIN, or 'cancel'.")
        else:
            self._speak(f"I need your approval to {action}. Say 'approve' to continue or 'cancel' to abort.")

        # Start timeout timer
        self._timer = threading.Timer(APPROVAL_TIMEOUT, self._on_timeout)
        self._timer.start()

        log_self_heal(f"Approval requested for: {action}")
        return True

    def _cancel_timer(self):
        """Cancel pending timeout."""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _on_timeout(self):
        """Handle approval timeout."""
        if self._pending:
            action = self._pending.action
            self._pending = None
            self._callback_on_confirm = None
            self._callback_on_deny = None
            self._speak("Approval timed out. Action cancelled.")
            log_self_heal(f"Approval timeout for: {action}")

    def check_response(self, text: str) -> Tuple[bool, str]:
        """
        Check if user response is approval or denial.
        Returns (handled, result) where result is 'approved', 'denied', or 'invalid'.
        """
        if not self._pending:
            return False, ""

        text_lower = text.lower().strip()
        words = text_lower.split()

        # Check for PIN if required
        if self._pending.requires_pin and APPROVAL_PIN:
            # Look for PIN in response
            pin_found = APPROVAL_PIN in text_lower.replace(" ", "")
            if not pin_found:
                # Check if this looks like a confirmation attempt
                if any(phrase in text_lower for phrase in self.CONFIRM_PHRASES):
                    self._speak("Please include your PIN to confirm this action.")
                    return True, "need_pin"
                # Not a confirmation attempt, let it pass through
                return False, ""

        # Check for confirmation
        if any(phrase in text_lower for phrase in self.CONFIRM_PHRASES):
            self._cancel_timer()
            action = self._pending.action
            callback = self._callback_on_confirm

            # Log approval
            self._log_approval(action, approved=True)

            self._pending = None
            self._callback_on_confirm = None
            self._callback_on_deny = None

            self._speak(f"Approved. Executing {action}.")
            log_self_heal(f"User approved: {action}")

            if callback:
                try:
                    callback()
                except Exception as e:
                    log_self_heal(f"Approval callback error: {e}", "ERROR")

            return True, "approved"

        # Check for denial
        if any(phrase in text_lower for phrase in self.DENY_PHRASES):
            self._cancel_timer()
            action = self._pending.action
            callback = self._callback_on_deny

            # Log denial
            self._log_approval(action, approved=False)

            self._pending = None
            self._callback_on_confirm = None
            self._callback_on_deny = None

            self._speak("Cancelled.")
            log_self_heal(f"User denied: {action}")

            if callback:
                try:
                    callback()
                except Exception as e:
                    log_self_heal(f"Denial callback error: {e}", "ERROR")

            return True, "denied"

        # Not a clear response
        return False, ""

    def _log_approval(self, action: str, approved: bool):
        """Log approval decision for audit."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "approved": approved,
            "session_id": os.getenv("SESSION_ID", "default")
        }
        self._approval_log.append(entry)

        # Write to file
        log_file = Path(__file__).parent.parent / "logs" / "approval_log.json"
        try:
            import json
            existing = []
            if log_file.exists():
                try:
                    existing = json.loads(log_file.read_text())
                except:
                    pass
            existing.append(entry)
            log_file.write_text(json.dumps(existing, indent=2))
        except Exception as e:
            log_self_heal(f"Failed to write approval log: {e}", "ERROR")

    def is_pending(self) -> bool:
        """Check if approval is pending."""
        return self._pending is not None

    def get_pending_action(self) -> Optional[str]:
        """Get the action awaiting approval."""
        return self._pending.action if self._pending else None

    def cancel_pending(self):
        """Cancel any pending approval request."""
        self._cancel_timer()
        if self._pending:
            log_self_heal(f"Pending approval cancelled: {self._pending.action}")
        self._pending = None
        self._callback_on_confirm = None
        self._callback_on_deny = None


# Singleton
_manager: Optional[ApprovalManager] = None

def get_approval_manager() -> ApprovalManager:
    global _manager
    if _manager is None:
        _manager = ApprovalManager()
    return _manager
