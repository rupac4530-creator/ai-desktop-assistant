# safety/confirmations.py
"""Confirmation flows for dangerous operations."""

import time
import threading
from typing import Callable, Optional
from enum import Enum


class ConfirmationResult(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DENIED = "denied"
    TIMEOUT = "timeout"


# Dangerous step types that require confirmation
DANGEROUS_STEP_TYPES = {
    'delete_file', 'delete_folder', 'run_command', 'install_package',
    'fill_credentials', 'login', 'shutdown', 'restart', 'edit_file',
    'format_drive', 'uninstall', 'remove', 'kill_process'
}

# Keywords that indicate dangerous commands
DANGEROUS_KEYWORDS = [
    'delete', 'remove', 'shutdown', 'restart', 'format', 'kill',
    'uninstall', 'rm ', 'rmdir', 'del ', 'erase', 'wipe',
    # Hindi
    'हटाओ', 'मिटाओ', 'बंद करो'
]


class ConfirmationManager:
    """Manage confirmation requests with timeout."""
    
    def __init__(self, default_timeout: float = 10.0):
        self.default_timeout = default_timeout
        self.pending_confirmation: Optional[dict] = None
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._result: ConfirmationResult = ConfirmationResult.PENDING
        self._callback: Optional[Callable] = None
    
    def request_confirmation(
        self,
        action_description: str,
        on_result: Callable[[ConfirmationResult], None] = None,
        timeout: float = None
    ) -> bool:
        """
        Request confirmation for an action.
        
        Args:
            action_description: Description of what will happen
            on_result: Callback when result is received
            timeout: Timeout in seconds (default: self.default_timeout)
        
        Returns:
            True if confirmation request was created
        """
        with self._lock:
            if self.pending_confirmation:
                print("[Safety] Already waiting for confirmation")
                return False
            
            self.pending_confirmation = {
                'description': action_description,
                'created_at': time.time(),
                'timeout': timeout or self.default_timeout
            }
            self._result = ConfirmationResult.PENDING
            self._callback = on_result
            
            # Start timeout timer
            self._timer = threading.Timer(
                timeout or self.default_timeout,
                self._on_timeout
            )
            self._timer.start()
            
            print(f"[Safety] ⚠️  CONFIRMATION REQUIRED")
            print(f"[Safety] Action: {action_description}")
            print(f"[Safety] Say 'yes' or 'no' (timeout: {timeout or self.default_timeout}s)")
            
            return True
    
    def respond(self, response: str) -> ConfirmationResult:
        """
        Process a confirmation response.
        
        Args:
            response: User response (yes/no/y/n/हाँ/नहीं)
        
        Returns:
            The result of the confirmation
        """
        with self._lock:
            if not self.pending_confirmation:
                return ConfirmationResult.PENDING
            
            # Cancel timeout timer
            if self._timer:
                self._timer.cancel()
                self._timer = None
            
            # Parse response
            response_lower = response.lower().strip()
            
            if response_lower in ['yes', 'y', 'हाँ', 'हां', 'ha', 'haan', 'kar do', 'karo', 'okay', 'ok', 'confirm']:
                self._result = ConfirmationResult.CONFIRMED
                print("[Safety] ✓ Action CONFIRMED")
            elif response_lower in ['no', 'n', 'नहीं', 'nahi', 'cancel', 'stop', 'mat karo', 'ruk']:
                self._result = ConfirmationResult.DENIED
                print("[Safety] ✗ Action DENIED")
            else:
                # Unclear response - treat as denied for safety
                self._result = ConfirmationResult.DENIED
                print(f"[Safety] ✗ Unclear response '{response}' - treating as DENIED")
            
            # Callback
            if self._callback:
                self._callback(self._result)
            
            self.pending_confirmation = None
            return self._result
    
    def _on_timeout(self):
        """Handle confirmation timeout."""
        with self._lock:
            if self.pending_confirmation:
                self._result = ConfirmationResult.TIMEOUT
                print("[Safety] ⏰ Confirmation TIMEOUT - action cancelled")
                
                if self._callback:
                    self._callback(self._result)
                
                self.pending_confirmation = None
    
    def is_pending(self) -> bool:
        """Check if confirmation is pending."""
        return self.pending_confirmation is not None
    
    def get_result(self) -> ConfirmationResult:
        """Get the last confirmation result."""
        return self._result
    
    def cancel(self):
        """Cancel pending confirmation."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            
            if self.pending_confirmation:
                self._result = ConfirmationResult.DENIED
                if self._callback:
                    self._callback(self._result)
                self.pending_confirmation = None
                print("[Safety] Confirmation cancelled")


def is_dangerous_action(action_type: str) -> bool:
    """Check if an action type requires confirmation."""
    return action_type.lower() in DANGEROUS_STEP_TYPES


def contains_dangerous_keywords(text: str) -> bool:
    """Check if text contains dangerous keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in DANGEROUS_KEYWORDS)


def require_confirmation(func: Callable) -> Callable:
    """
    Decorator to require confirmation before executing a function.
    
    Usage:
        @require_confirmation
        def dangerous_operation():
            ...
    """
    manager = ConfirmationManager()
    
    def wrapper(*args, **kwargs):
        # Create event to wait for confirmation
        confirmed = threading.Event()
        result = [None]
        
        def on_result(conf_result):
            result[0] = conf_result
            confirmed.set()
        
        # Request confirmation
        desc = f"Execute {func.__name__}?"
        manager.request_confirmation(desc, on_result)
        
        # Wait for response (blocking)
        confirmed.wait()
        
        if result[0] == ConfirmationResult.CONFIRMED:
            return func(*args, **kwargs)
        else:
            print(f"[Safety] {func.__name__} cancelled")
            return None
    
    return wrapper


# Global confirmation manager for the assistant
_global_manager: Optional[ConfirmationManager] = None


def get_confirmation_manager() -> ConfirmationManager:
    """Get the global confirmation manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ConfirmationManager()
    return _global_manager


def request_confirmation(description: str, callback: Callable = None, timeout: float = 10.0) -> bool:
    """Request confirmation using global manager."""
    return get_confirmation_manager().request_confirmation(description, callback, timeout)


def respond_to_confirmation(response: str) -> ConfirmationResult:
    """Respond to pending confirmation."""
    return get_confirmation_manager().respond(response)


def is_confirmation_pending() -> bool:
    """Check if confirmation is pending."""
    return get_confirmation_manager().is_pending()
