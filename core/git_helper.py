# core/git_helper.py
"""
Git Helper - Provides Git operations for the autonomous coder.
Handles branches, commits, snapshots, merges, and rollbacks.
"""

import os
import sys
import time
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

# Project root
ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
SNAPSHOTS_DIR = LOGS_DIR / "snapshots"

# Git executable path (add to PATH if needed)
GIT_PATH = os.getenv("GIT_PATH", "git")

# Rate limiting
MAX_COMMITS_PER_HOUR = 3
MAX_LINES_PER_COMMIT = 500
_commit_timestamps: List[datetime] = []


def _run(cmd: str, check: bool = True) -> str:
    """Run a git command and return output."""
    # Ensure git is in PATH
    env = os.environ.copy()
    if "E:\\Git\\bin" not in env.get("PATH", ""):
        env["PATH"] = "E:\\Git\\bin;E:\\Git\\cmd;" + env.get("PATH", "")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise Exception(f"Git command timed out: {cmd}")


def is_git_repo() -> bool:
    """Check if we're in a git repo."""
    return (ROOT / ".git").exists()


def get_current_branch() -> str:
    """Get current branch name."""
    return _run("git rev-parse --abbrev-ref HEAD")


def get_current_commit() -> str:
    """Get current commit hash."""
    return _run("git rev-parse --verify HEAD")


def get_commit_count() -> int:
    """Get total number of commits."""
    try:
        return int(_run("git rev-list --count HEAD"))
    except:
        return 0


def snapshot_repo(tag: Optional[str] = None) -> str:
    """
    Create a zip backup of the current repo state.
    
    Args:
        tag: Optional tag for the snapshot name
        
    Returns:
        Path to the created zip file
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"{ts}_{tag}" if tag else f"{ts}_git_backup"
    
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create zip excluding venv, logs, .git
    out_path = SNAPSHOTS_DIR / f"{label}.zip"
    
    # Create archive of tracked files only
    try:
        # Use git archive for clean snapshot
        archive_cmd = f'git archive --format=zip HEAD -o "{out_path}"'
        _run(archive_cmd)
    except:
        # Fallback: manual zip
        temp_dir = SNAPSHOTS_DIR / f"{label}_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Copy tracked files
        tracked = _run("git ls-files").split("\n")
        for f in tracked[:500]:  # Limit files
            if f:
                src = ROOT / f
                dst = temp_dir / f
                if src.exists() and src.is_file():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
        
        shutil.make_archive(str(out_path).replace('.zip', ''), 'zip', temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return str(out_path)


def start_autobranch(prefix: str = "ai-autofix") -> str:
    """
    Create a new branch for autonomous changes.
    
    Args:
        prefix: Branch prefix
        
    Returns:
        New branch name
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    branch_name = f"{prefix}/{ts}"
    
    # Make sure we're on main first
    try:
        _run("git checkout main", check=False)
    except:
        pass
    
    # Create and checkout new branch
    _run(f"git checkout -b {branch_name}")
    
    return branch_name


def commit_patch(msg: str, files: Optional[List[str]] = None) -> Tuple[str, bool]:
    """
    Stage and commit changes.
    
    Args:
        msg: Commit message
        files: Specific files to add, or None for all
        
    Returns:
        Tuple of (commit_hash, success)
    """
    global _commit_timestamps
    
    # Check rate limit
    now = datetime.now()
    _commit_timestamps = [t for t in _commit_timestamps if (now - t).seconds < 3600]
    if len(_commit_timestamps) >= MAX_COMMITS_PER_HOUR:
        return "", False
    
    # Check line count
    diff_stat = _run("git diff --stat", check=False)
    lines_changed = 0
    for line in diff_stat.split("\n"):
        if "insertion" in line or "deletion" in line:
            parts = line.split()
            for p in parts:
                if p.isdigit():
                    lines_changed += int(p)
    
    if lines_changed > MAX_LINES_PER_COMMIT:
        print(f"[Git] Patch too large: {lines_changed} lines (max {MAX_LINES_PER_COMMIT})")
        return "", False
    
    # Stage files
    if files:
        for f in files:
            _run(f'git add "{f}"', check=False)
    else:
        _run("git add -A")
    
    # Check if there are staged changes
    status = _run("git status --porcelain")
    if not status:
        return get_current_commit(), True
    
    # Commit
    try:
        _run(f'git commit -m "{msg}"')
        _commit_timestamps.append(now)
        return get_current_commit(), True
    except Exception as e:
        print(f"[Git] Commit failed: {e}")
        return "", False


def merge_branch(branch: str, into: str = "main") -> bool:
    """
    Merge a branch into target (default: main).
    
    Args:
        branch: Branch to merge
        into: Target branch
        
    Returns:
        Success status
    """
    try:
        _run(f"git checkout {into}")
        _run(f"git merge --no-ff {branch} -m 'ai: merge {branch}'")
        _run(f"git branch -d {branch}", check=False)
        return True
    except Exception as e:
        print(f"[Git] Merge failed: {e}")
        return False


def rollback_to(commit: str) -> bool:
    """
    Hard reset to a specific commit.
    
    Args:
        commit: Commit hash to reset to
        
    Returns:
        Success status
    """
    try:
        _run(f"git reset --hard {commit}")
        return True
    except Exception as e:
        print(f"[Git] Rollback failed: {e}")
        return False


def get_changed_files() -> List[str]:
    """Get list of changed files (staged + unstaged)."""
    status = _run("git status --porcelain", check=False)
    files = []
    for line in status.split("\n"):
        if line.strip():
            # Format: "XY filename" or "XY original -> renamed"
            parts = line[3:].split(" -> ")
            files.append(parts[-1].strip())
    return files


def get_diff_stats() -> dict:
    """Get statistics about current changes."""
    try:
        stat = _run("git diff --stat", check=False)
        numstat = _run("git diff --numstat", check=False)
        
        insertions = 0
        deletions = 0
        files = 0
        
        for line in numstat.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    try:
                        insertions += int(parts[0]) if parts[0] != '-' else 0
                        deletions += int(parts[1]) if parts[1] != '-' else 0
                        files += 1
                    except:
                        pass
        
        return {
            "files_changed": files,
            "insertions": insertions,
            "deletions": deletions,
            "total_lines": insertions + deletions,
        }
    except:
        return {"files_changed": 0, "insertions": 0, "deletions": 0, "total_lines": 0}


def log_git_action(action: str, details: dict):
    """Log a git action to the audit trail."""
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / "git_actions.jsonl"
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "branch": get_current_branch(),
        "commit": get_current_commit(),
        **details,
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_status() -> dict:
    """Get current git status."""
    return {
        "is_repo": is_git_repo(),
        "branch": get_current_branch() if is_git_repo() else None,
        "commit": get_current_commit() if is_git_repo() else None,
        "commit_count": get_commit_count(),
        "changed_files": get_changed_files(),
        "diff_stats": get_diff_stats(),
        "commits_this_hour": len(_commit_timestamps),
        "max_commits_per_hour": MAX_COMMITS_PER_HOUR,
    }


if __name__ == "__main__":
    print("=== Git Helper Status ===")
    status = get_status()
    print(json.dumps(status, indent=2))
