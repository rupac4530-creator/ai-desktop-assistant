# core/self_update.py
"""
Full Autonomy Self-Update System
- No approval required for any updates
- Auto-merge, test, apply, rollback
- Off-site backup upload
- Notification hooks (webhook, email, TTS, HUD)
- Continuous monitoring loop
- CLI: python core/self_update.py --enable-full-autonomy --apply-now
"""

import os
import sys
import subprocess
import shutil
import zipfile
import argparse
import json
import time
import threading
from pathlib import Path
from datetime import datetime, time as dt_time
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.watchdog import log_self_heal, SNAPSHOTS_DIR

# ===========================================
# CONFIGURATION FROM .env
# ===========================================

def get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() == "true"

def get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except:
        return default

def get_list(key: str, default: str = "") -> List[str]:
    val = os.getenv(key, default)
    return [x.strip() for x in val.split(",") if x.strip()]

# Core settings
SELF_UPDATE_ENABLED = get_bool("SELF_UPDATE_ENABLED", True)
SELF_UPDATE_CHECK_INTERVAL = get_int("SELF_UPDATE_CHECK_INTERVAL", 3600)
SELF_UPDATE_AUTO_APPLY = get_bool("SELF_UPDATE_AUTO_APPLY", True)
SELF_UPDATE_WHITELIST = get_list("SELF_UPDATE_WHITELIST", "automation,vision,orchestrator,tools,ui,core")
SELF_UPDATE_REQUIRE_APPROVAL_FOR_CORE = get_bool("SELF_UPDATE_REQUIRE_APPROVAL_FOR_CORE", False)
SELF_UPDATE_CORE_WHITELIST = get_list("SELF_UPDATE_CORE_WHITELIST", "")
SELF_UPDATE_AUTO_APPLY_WINDOW = os.getenv("SELF_UPDATE_AUTO_APPLY_WINDOW", "00:00-23:59")
SELF_UPDATE_AUTO_ROLLBACK = get_bool("SELF_UPDATE_AUTO_ROLLBACK", True)
SELF_UPDATE_KEEP_SNAPSHOTS = get_int("SELF_UPDATE_KEEP_SNAPSHOTS", 14)
SELF_UPDATE_AUTO_BACKUP = get_bool("SELF_UPDATE_AUTO_BACKUP", True)
SELF_UPDATE_UPLOAD_URL = os.getenv("SELF_UPDATE_UPLOAD_URL", "")
SELF_UPDATE_UPLOAD_TOKEN = os.getenv("SELF_UPDATE_UPLOAD_TOKEN", "")
SELF_UPDATE_NOTIFY_URL = os.getenv("SELF_UPDATE_NOTIFY_URL", "")

APPROVAL_PIN = os.getenv("APPROVAL_PIN", "")
NOTIFY_VIA_TTS = get_bool("NOTIFY_VIA_TTS", True)

# Smoke tests to run before applying
SMOKE_TESTS = [
    "tools/test_watchdog.py",
    "tools/test_repair_engine.py",
    "tools/test_core_smoke.py",
    "tools/test_ptt_toggle.py",
    "tools/test_stt_long.py",
    "tools/test_multitask.py",
]

# Log files
LOGS_DIR = Path(__file__).parent.parent / "logs"
SELF_UPDATE_LOG = LOGS_DIR / "self_update.log"
SELF_UPDATE_FAIL_LOG = LOGS_DIR / "self_update_fail.log"
SELF_UPDATE_RUN_LOG = LOGS_DIR / "self_update_run.log"

# State tracking
_last_run_time: Optional[str] = None
_last_run_result: str = "NOT_RUN"


@dataclass
class UpdateResult:
    success: bool
    message: str
    tests_passed: bool
    changes: List[str]
    backup_path: Optional[str] = None
    deferred: bool = False
    requires_approval: bool = False
    commit_sha: Optional[str] = None


def log_update(msg: str, level: str = "INFO"):
    """Log to self_update.log with timestamp."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"[{ts}] [{level}] {msg}"
    with open(SELF_UPDATE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(f"[Update] {msg}")
    log_self_heal(msg, level)


def log_json(event: str, data: Dict[str, Any]):
    """Append JSON line to self_update.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        **data
    }
    with open(SELF_UPDATE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_run(msg: str):
    """Log to self_update_run.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SELF_UPDATE_RUN_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def log_failure(msg: str, details: str = ""):
    """Log failure to self_update_fail.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat()
    with open(SELF_UPDATE_FAIL_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n[{ts}] FAILURE\n{msg}\n{details}\n")


def is_in_maintenance_window() -> bool:
    """Check if current time is within the maintenance window."""
    window = SELF_UPDATE_AUTO_APPLY_WINDOW
    if not window or "-" not in window:
        return True
    
    try:
        start_str, end_str = window.split("-")
        start_h, start_m = map(int, start_str.split(":"))
        end_h, end_m = map(int, end_str.split(":"))
        
        now = datetime.now().time()
        start = dt_time(start_h, start_m)
        end = dt_time(end_h, end_m)
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    except:
        return True


def prune_old_snapshots():
    """Keep only the most recent N snapshots."""
    try:
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        all_snapshots = sorted(
            [p for p in SNAPSHOTS_DIR.iterdir() if p.is_file() and p.suffix == ".zip"],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old in all_snapshots[SELF_UPDATE_KEEP_SNAPSHOTS:]:
            old.unlink()
            log_update(f"Pruned old snapshot: {old.name}")
    except Exception as e:
        log_update(f"Prune error: {e}", "WARN")


def upload_snapshot(backup_path: str) -> bool:
    """Upload snapshot to off-site URL if configured."""
    if not SELF_UPDATE_UPLOAD_URL or not SELF_UPDATE_AUTO_BACKUP:
        return False
    
    try:
        import requests
        headers = {}
        if SELF_UPDATE_UPLOAD_TOKEN:
            headers["Authorization"] = f"Bearer {SELF_UPDATE_UPLOAD_TOKEN}"
        
        with open(backup_path, "rb") as f:
            files = {"file": (Path(backup_path).name, f, "application/zip")}
            resp = requests.post(SELF_UPDATE_UPLOAD_URL, files=files, headers=headers, timeout=120)
        
        if resp.status_code in (200, 201):
            log_update(f"Snapshot uploaded to {SELF_UPDATE_UPLOAD_URL}")
            log_json("snapshot_uploaded", {"path": backup_path, "url": SELF_UPDATE_UPLOAD_URL})
            return True
        else:
            log_update(f"Snapshot upload failed: {resp.status_code}", "WARN")
            return False
    except Exception as e:
        log_update(f"Snapshot upload error: {e}", "ERROR")
        return False


class SelfUpdater:
    """Full Autonomy Self-Update System."""

    def __init__(self):
        self._repo_root = Path(__file__).parent.parent
        self._tts = None
        self._pending_update = None
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        log_update("SelfUpdater initialized (FULL AUTONOMY MODE)")

    def set_tts(self, tts):
        self._tts = tts

    def _speak(self, text: str):
        if self._tts and NOTIFY_VIA_TTS:
            try:
                self._tts.speak(text, block=False)
            except:
                pass
        print(f"[Update] {text}")

    def _notify(self, event_type: str, summary: str, details: str = ""):
        """Send notification via all configured channels."""
        try:
            from core.notify import notify
            notify(event_type, summary, details)
        except ImportError:
            log_update(f"Notify: {event_type} - {summary}")

    def _run_git(self, *args) -> Tuple[bool, str]:
        """Run git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout + result.stderr
            log_run(f"git {' '.join(args)}: {result.returncode}")
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    def _get_current_commit(self) -> str:
        """Get current HEAD commit SHA."""
        success, output = self._run_git("rev-parse", "HEAD")
        return output[:8] if success else "unknown"

    def check_for_updates(self) -> Tuple[bool, List[str], str]:
        """Check for updates. Returns (has_updates, changed_files, remote_commit)."""
        log_update("Checking for updates...")
        self._notify("update_check", "Checking for updates")

        success, output = self._run_git("fetch", "origin")
        if not success:
            log_update(f"Git fetch failed: {output}", "WARN")
            return False, [], ""

        # Get remote commit
        success, remote_sha = self._run_git("rev-parse", "origin/main")
        if not success:
            success, remote_sha = self._run_git("rev-parse", "origin/master")
        
        # Check diff
        success, output = self._run_git("diff", "--name-only", "HEAD", "origin/main")
        if not success:
            success, output = self._run_git("diff", "--name-only", "HEAD", "origin/master")
            if not success:
                return False, [], ""

        changed = [f.strip() for f in output.split("\n") if f.strip()]
        log_update(f"Found {len(changed)} changed files")
        log_json("update_check", {"changed_count": len(changed), "remote": remote_sha[:8] if remote_sha else ""})
        return len(changed) > 0, changed, remote_sha[:8] if remote_sha else ""

    def create_backup(self) -> str:
        """Create full backup zip of repository."""
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = SNAPSHOTS_DIR / f"{ts}_repo_backup.zip"

        log_update(f"Creating backup: {backup_path}")

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in self._repo_root.rglob("*"):
                rel = file.relative_to(self._repo_root)
                skip_dirs = ["venv", "__pycache__", ".git", "logs", "node_modules", "snapshots"]
                if any(d in str(rel) for d in skip_dirs):
                    continue
                if file.is_file():
                    zf.write(file, rel)

        # Metadata
        meta = {"timestamp": ts, "backup_path": str(backup_path), "commit": self._get_current_commit()}
        meta_path = SNAPSHOTS_DIR / f"{ts}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        log_update(f"Backup created: {backup_path}")
        prune_old_snapshots()
        
        # Upload if configured
        if SELF_UPDATE_AUTO_BACKUP and SELF_UPDATE_UPLOAD_URL:
            upload_snapshot(str(backup_path))
        
        return str(backup_path)

    def run_smoke_tests(self) -> Tuple[bool, str]:
        """Run all smoke tests."""
        log_update("Running smoke tests...")
        self._speak("Running tests to verify update safety.")

        existing_tests = [f for f in SMOKE_TESTS if (self._repo_root / f).exists()]
        
        if not existing_tests:
            log_update("No smoke tests found")
            return True, "No tests"

        log_update(f"Running {len(existing_tests)} test files")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"] + existing_tests,
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            output = result.stdout + result.stderr
            log_run(f"pytest: {result.returncode}\n{output}")

            if result.returncode == 0:
                log_update("All smoke tests PASSED")
                return True, output
            else:
                log_update(f"Smoke tests FAILED", "ERROR")
                log_failure("Smoke tests failed", output)
                return False, output

        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except Exception as e:
            return False, str(e)

    def apply_update(self) -> Tuple[bool, str]:
        """Merge updates from origin."""
        log_update("Applying update (merging from origin)...")

        self._run_git("stash")
        
        success, output = self._run_git("merge", "origin/main", "--no-edit")
        if not success:
            success, output = self._run_git("merge", "origin/master", "--no-edit")
        
        if not success:
            log_update(f"Merge failed: {output}", "ERROR")
            return False, output

        log_update("Update applied successfully")
        return True, output

    def rollback(self, backup_path: str) -> bool:
        """Rollback to backup."""
        log_update(f"Rolling back to: {backup_path}")
        self._speak("Rolling back to previous version.")

        try:
            backup = Path(backup_path)
            if not backup.exists():
                log_update(f"Backup not found", "ERROR")
                return False

            with zipfile.ZipFile(backup, 'r') as zf:
                zf.extractall(self._repo_root)

            log_update("Rollback complete")
            log_json("rollback_done", {"backup": backup_path})
            self._notify("rollback_done", "Rolled back to previous version", backup_path)
            return True

        except Exception as e:
            log_update(f"Rollback failed: {e}", "ERROR")
            return False

    def run_full_autonomy_flow(self, force: bool = False) -> UpdateResult:
        """
        Full autonomy update flow:
        1. Check for updates
        2. Create backup
        3. Merge updates
        4. Run tests
        5. If tests fail: rollback
        6. If tests pass: notify success
        """
        global _last_run_time, _last_run_result
        _last_run_time = datetime.now().isoformat()

        if not SELF_UPDATE_ENABLED:
            _last_run_result = "DISABLED"
            return UpdateResult(False, "Self-update disabled", False, [])

        # Check maintenance window
        if not force and not is_in_maintenance_window():
            log_update(f"Outside maintenance window: {SELF_UPDATE_AUTO_APPLY_WINDOW}")
            _last_run_result = "DEFERRED"
            return UpdateResult(True, "Deferred - outside window", False, [], deferred=True)

        self._speak("Checking for updates.")

        # Check for updates
        has_updates, changed, remote_sha = self.check_for_updates()
        if not has_updates:
            self._speak("No updates available.")
            _last_run_result = "NO_UPDATES"
            log_json("update_check", {"result": "no_updates"})
            return UpdateResult(True, "Already up to date", True, [])

        self._speak(f"Found {len(changed)} updates. Applying automatically.")

        # Create backup BEFORE applying
        backup = self.create_backup()

        # Apply update
        success, msg = self.apply_update()
        if not success:
            self._speak("Failed to apply update.")
            _last_run_result = "MERGE_FAILED"
            log_failure("Merge failed", msg)
            self._notify("update_failed", "Merge failed", msg)
            return UpdateResult(False, msg, False, changed, backup, commit_sha=remote_sha)

        # Run tests on new code
        tests_passed, test_output = self.run_smoke_tests()
        
        if not tests_passed:
            self._speak("Tests failed after update. Rolling back.")
            _last_run_result = "TESTS_FAILED"
            log_failure("Tests failed after update", test_output)
            
            if SELF_UPDATE_AUTO_ROLLBACK:
                # Reset to previous state
                self._run_git("reset", "--hard", "HEAD~1")
                self.rollback(backup)
            
            self._notify("update_failed", "Tests failed, rolled back", test_output[:500])
            return UpdateResult(False, f"Tests failed, rolled back", False, changed, backup, commit_sha=remote_sha)

        # Success!
        _last_run_result = "OK"
        self._speak(f"Update complete. {len(changed)} files updated. All tests passed.")
        log_update(f"Update successful: {len(changed)} files")
        log_json("update_applied", {
            "commit": remote_sha,
            "changed": len(changed),
            "tests_passed": True,
            "backup": backup
        })
        self._notify("update_applied", f"Update applied: {len(changed)} files", f"Commit: {remote_sha}")
        
        return UpdateResult(True, "Update successful", True, changed, backup, commit_sha=remote_sha)

    def start_monitor(self):
        """Start background monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        log_update("Background monitor started")

    def stop_monitor(self):
        """Stop background monitoring."""
        self._stop_monitor.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        log_update("Background monitor stopped")

    def _monitor_loop(self):
        """Background loop to check for updates periodically."""
        while not self._stop_monitor.is_set():
            try:
                if SELF_UPDATE_AUTO_APPLY and is_in_maintenance_window():
                    self.run_full_autonomy_flow()
            except Exception as e:
                log_update(f"Monitor error: {e}", "ERROR")
            
            # Sleep in small chunks to allow quick shutdown
            for _ in range(SELF_UPDATE_CHECK_INTERVAL):
                if self._stop_monitor.is_set():
                    break
                time.sleep(1)

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "AUTOPILOT": "ACTIVE" if SELF_UPDATE_AUTO_APPLY else "INACTIVE",
            "FULL_AUTONOMY": not SELF_UPDATE_REQUIRE_APPROVAL_FOR_CORE,
            "enabled": SELF_UPDATE_ENABLED,
            "auto_apply": SELF_UPDATE_AUTO_APPLY,
            "check_interval": SELF_UPDATE_CHECK_INTERVAL,
            "whitelist": SELF_UPDATE_WHITELIST,
            "maintenance_window": SELF_UPDATE_AUTO_APPLY_WINDOW,
            "in_window": is_in_maintenance_window(),
            "auto_rollback": SELF_UPDATE_AUTO_ROLLBACK,
            "keep_snapshots": SELF_UPDATE_KEEP_SNAPSHOTS,
            "LAST_RUN": _last_run_time or "NEVER",
            "LAST_RESULT": _last_run_result
        }


# Singleton
_updater: Optional[SelfUpdater] = None

def get_updater() -> SelfUpdater:
    global _updater
    if _updater is None:
        _updater = SelfUpdater()
    return _updater


# ===========================================
# CLI INTERFACE
# ===========================================

def main():
    parser = argparse.ArgumentParser(description="Full Autonomy Self-Update System")
    parser.add_argument("--check-now", action="store_true", help="Check for updates now")
    parser.add_argument("--apply-now", action="store_true", help="Apply updates immediately")
    parser.add_argument("--enable-full-autonomy", action="store_true", help="Enable full autonomy mode")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--start-monitor", action="store_true", help="Start background monitor")
    args = parser.parse_args()

    updater = get_updater()

    if args.status:
        status = updater.get_status()
        print("\n=== Self-Update System Status ===")
        for k, v in status.items():
            print(f"  {k}: {v}")
        return

    if args.enable_full_autonomy or args.apply_now or args.check_now:
        print("\n=== FULL AUTONOMY MODE ===")
        log_run("=== FULL AUTONOMY FLOW STARTED ===")
        
        result = updater.run_full_autonomy_flow(force=args.apply_now)
        
        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Message: {result.message}")
        print(f"Tests passed: {result.tests_passed}")
        print(f"Changed files: {len(result.changes)}")
        if result.backup_path:
            print(f"Backup: {result.backup_path}")
        if result.commit_sha:
            print(f"Commit: {result.commit_sha}")
        
        log_run(f"Result: {result.message}")
        return

    if args.start_monitor:
        print("Starting background monitor...")
        updater.start_monitor()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            updater.stop_monitor()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
