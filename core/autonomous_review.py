# core/autonomous_review.py
"""
Autonomous Review - Generates human-readable reports from logs.
Creates daily digests and converts patch logs to reports.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
PATCH_LOG = LOGS_DIR / "autonomous_patch_log.jsonl"
DIGEST_FILE = LOGS_DIR / "autonomous_digest.txt"


def load_patch_logs(days: int = 1) -> List[Dict]:
    """Load patch logs from the last N days."""
    if not PATCH_LOG.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    
    with open(PATCH_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time >= cutoff:
                    entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue
    
    return entries


def generate_report(entries: List[Dict]) -> str:
    """Generate a human-readable report from patch log entries."""
    if not entries:
        return "No autonomous actions recorded in this period."
    
    lines = ["=" * 60]
    lines.append("AUTONOMOUS BRAIN ACTIVITY REPORT")
    lines.append("=" * 60)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Entries: {len(entries)}")
    lines.append("")
    
    # Summary stats
    actions = defaultdict(int)
    models = defaultdict(int)
    files_changed = set()
    rollbacks = 0
    
    for entry in entries:
        actions[entry.get("action", "unknown")] += 1
        models[entry.get("llm_model_used", "unknown")] += 1
        files_changed.update(entry.get("patch_files", []))
        if entry.get("rollback_flag"):
            rollbacks += 1
    
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total actions: {len(entries)}")
    lines.append(f"Rollbacks: {rollbacks}")
    lines.append(f"Files touched: {len(files_changed)}")
    lines.append("")
    
    lines.append("Actions by type:")
    for action, count in sorted(actions.items()):
        lines.append(f"  - {action}: {count}")
    lines.append("")
    
    lines.append("Models used:")
    for model, count in sorted(models.items()):
        lines.append(f"  - {model}: {count}")
    lines.append("")
    
    # Detailed entries
    lines.append("DETAILED LOG")
    lines.append("-" * 40)
    
    for entry in entries:
        ts = entry.get("timestamp", "unknown")
        action = entry.get("action", "unknown")
        files = entry.get("patch_files", [])
        result = entry.get("tests_result", "unknown")
        explanation = entry.get("explanation_text", "")[:100]
        rollback = "ROLLED BACK" if entry.get("rollback_flag") else ""
        
        lines.append(f"\n[{ts}] {action} {rollback}")
        lines.append(f"  Files: {', '.join(files) if files else 'none'}")
        lines.append(f"  Tests: {result}")
        if explanation:
            lines.append(f"  Note: {explanation}")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    
    return "\n".join(lines)


def generate_daily_digest() -> str:
    """Generate and save a daily digest."""
    entries = load_patch_logs(days=1)
    report = generate_report(entries)
    
    # Save to file
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Archive previous digest
    if DIGEST_FILE.exists():
        archive_name = f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        DIGEST_FILE.rename(LOGS_DIR / archive_name)
    
    DIGEST_FILE.write_text(report, encoding="utf-8")
    
    return report


def get_recent_summary(hours: int = 1) -> Dict[str, Any]:
    """Get a summary of recent activity."""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    if not PATCH_LOG.exists():
        return {
            "actions": 0,
            "rollbacks": 0,
            "files_changed": [],
            "last_action": None,
        }
    
    entries = []
    with open(PATCH_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time >= cutoff:
                    entries.append(entry)
            except:
                continue
    
    files_changed = set()
    rollbacks = 0
    last_action = None
    
    for entry in entries:
        files_changed.update(entry.get("patch_files", []))
        if entry.get("rollback_flag"):
            rollbacks += 1
        last_action = entry
    
    return {
        "actions": len(entries),
        "rollbacks": rollbacks,
        "files_changed": list(files_changed),
        "last_action": last_action,
    }


def speak_summary(summary: Dict[str, Any]):
    """Speak a brief summary via TTS."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        
        if summary["actions"] == 0:
            text = "No autonomous actions in the last hour."
        else:
            text = f"I performed {summary['actions']} actions in the last hour. "
            if summary["rollbacks"] > 0:
                text += f"{summary['rollbacks']} were rolled back. "
            if summary["files_changed"]:
                text += f"Modified {len(summary['files_changed'])} files."
        
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS] Failed: {e}")


if __name__ == "__main__":
    print("=== Autonomous Review ===\n")
    
    # Generate daily digest
    print("Generating daily digest...\n")
    report = generate_daily_digest()
    print(report)
    
    print(f"\nDigest saved to: {DIGEST_FILE}")
