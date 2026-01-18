# core/notify.py
"""
Notification helper for Full Autonomy system.
Sends notifications via webhook, email, TTS, and HUD.
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Configuration
NOTIFY_URL = os.getenv("SELF_UPDATE_NOTIFY_URL", "")
NOTIFY_TOKEN = os.getenv("SELF_UPDATE_UPLOAD_TOKEN", "")
NOTIFY_EMAIL = os.getenv("SELF_UPDATE_NOTIFY_EMAIL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_VIA_TTS = os.getenv("NOTIFY_VIA_TTS", "true").lower() == "true"
NOTIFY_VIA_HUD = os.getenv("NOTIFY_VIA_HUD", "true").lower() == "true"

LOGS_DIR = Path(__file__).parent.parent / "logs"
FAIL_LOG = LOGS_DIR / "self_update_fail.log"

# TTS reference
_tts = None

def set_tts(tts):
    """Set TTS engine reference."""
    global _tts
    _tts = tts


def notify(event_type: str, summary: str, details: str = ""):
    """
    Send notification via all configured channels.
    
    Event types: update_check, update_applied, update_failed, rollback_done, snapshot_uploaded
    """
    timestamp = datetime.now().isoformat()
    
    print(f"[Notify] {event_type}: {summary}")
    
    # Webhook notification
    if NOTIFY_URL:
        _send_webhook(event_type, summary, details, timestamp)
    
    # Email notification
    if NOTIFY_EMAIL and SMTP_HOST:
        _send_email(event_type, summary, details)
    
    # TTS notification
    if NOTIFY_VIA_TTS:
        _speak_notification(event_type, summary)
    
    # HUD notification
    if NOTIFY_VIA_HUD:
        _show_hud(event_type, summary)


def _send_webhook(event_type: str, summary: str, details: str, timestamp: str):
    """Send webhook POST notification."""
    try:
        import requests
        
        payload = {
            "event": event_type,
            "summary": summary,
            "details": details,
            "timestamp": timestamp,
            "source": "ai_desktop_assistant"
        }
        
        headers = {"Content-Type": "application/json"}
        if NOTIFY_TOKEN:
            headers["Authorization"] = f"Bearer {NOTIFY_TOKEN}"
        
        resp = requests.post(NOTIFY_URL, json=payload, headers=headers, timeout=10)
        
        if resp.status_code in (200, 201, 204):
            print(f"[Notify] Webhook sent: {event_type}")
        else:
            print(f"[Notify] Webhook failed: {resp.status_code}")
    
    except Exception as e:
        print(f"[Notify] Webhook error: {e}")


def _send_email(event_type: str, summary: str, details: str):
    """Send email notification."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL
        msg["Subject"] = f"[AI Assistant] {event_type}: {summary}"
        
        body = f"""
AI Desktop Assistant Notification
==================================
Event: {event_type}
Time: {datetime.now().isoformat()}
Summary: {summary}

Details:
{details}
"""
        msg.attach(MIMEText(body, "plain"))
        
        # Attach failure log if exists and event is failure
        if "fail" in event_type.lower() and FAIL_LOG.exists():
            with open(FAIL_LOG, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=self_update_fail.log")
            msg.attach(part)
        
        # Send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        print(f"[Notify] Email sent to {NOTIFY_EMAIL}")
    
    except Exception as e:
        print(f"[Notify] Email error: {e}")


def _speak_notification(event_type: str, summary: str):
    """Speak notification via TTS."""
    global _tts
    
    # Map event types to brief spoken phrases
    phrases = {
        "update_check": "Checking for updates.",
        "update_applied": f"Update applied. {summary}",
        "update_failed": f"Update failed. {summary}",
        "rollback_done": "Rolled back to previous version.",
        "snapshot_uploaded": "Backup uploaded.",
    }
    
    phrase = phrases.get(event_type, summary)
    
    if _tts:
        try:
            _tts.speak(phrase, block=False)
        except:
            pass
    else:
        # Try to get TTS
        try:
            from speech.local_tts import get_tts
            tts = get_tts()
            tts.speak(phrase, block=False)
        except:
            print(f"[TTS] {phrase}")


def _show_hud(event_type: str, summary: str):
    """Show HUD notification."""
    try:
        from ui.hud import get_hud
        hud = get_hud()
        if hud:
            hud.show_message(f"[{event_type}] {summary}", duration=5)
    except:
        pass  # HUD not available


# Convenience functions
def notify_update_check():
    notify("update_check", "Checking for updates")

def notify_update_applied(files_count: int, commit: str = ""):
    notify("update_applied", f"{files_count} files updated", f"Commit: {commit}")

def notify_update_failed(reason: str, details: str = ""):
    notify("update_failed", reason, details)

def notify_rollback(backup_path: str):
    notify("rollback_done", "Restored previous version", backup_path)

def notify_snapshot_uploaded(path: str, url: str):
    notify("snapshot_uploaded", f"Backup uploaded", f"Path: {path}, URL: {url}")
