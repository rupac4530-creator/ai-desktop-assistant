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


# ============================================================
# UPGRADE 1: Git Bisect - Automatic Bug Hunting
# ============================================================

def bisect_find_bad_commit(good_commit: str, test_command: str) -> Optional[str]:
    """
    Use git bisect to automatically find the commit that introduced a bug.
    
    Args:
        good_commit: A known-good commit hash
        test_command: Command to run (exit 0 = good, non-zero = bad)
    
    Returns:
        The commit hash that introduced the bug, or None
    """
    try:
        # Start bisect
        _run("git bisect start")
        _run("git bisect bad")  # Current HEAD is bad
        _run(f"git bisect good {good_commit}")
        
        # Run automated bisect
        result = _run(f"git bisect run {test_command}", check=False)
        
        # Extract the bad commit
        lines = result.split("\n")
        for line in lines:
            if "is the first bad commit" in line:
                # Get the commit hash from the next line or current state
                bad_commit = _run("git rev-parse refs/bisect/bad", check=False)
                _run("git bisect reset")
                
                log_git_action("bisect_found", {
                    "good_commit": good_commit,
                    "bad_commit": bad_commit,
                    "test_command": test_command,
                })
                return bad_commit
        
        _run("git bisect reset")
        return None
    except Exception as e:
        _run("git bisect reset", check=False)
        log_git_action("bisect_failed", {"error": str(e)})
        return None


def bisect_manual_step(is_good: bool) -> str:
    """Mark current commit as good or bad during manual bisect."""
    cmd = "git bisect good" if is_good else "git bisect bad"
    return _run(cmd)


# ============================================================
# UPGRADE 2: Diff-Aware Fixing (Mandatory Validation)
# ============================================================

def validate_diff_before_commit(expected_files: List[str]) -> Tuple[bool, str]:
    """
    Validate that the diff only touches expected files.
    ABORT if unrelated files are modified.
    
    Args:
        expected_files: List of files that SHOULD be changed
        
    Returns:
        (is_valid, reason)
    """
    changed = get_changed_files()
    
    if not changed:
        return False, "No changes detected"
    
    # Check for unexpected changes
    expected_set = set(str(Path(f).name) for f in expected_files)
    expected_paths = set(str(Path(f)) for f in expected_files)
    
    unexpected = []
    for f in changed:
        f_name = Path(f).name
        f_path = str(Path(f))
        if f_name not in expected_set and f_path not in expected_paths:
            # Check if it's a subpath match
            if not any(f_path.endswith(exp) for exp in expected_files):
                unexpected.append(f)
    
    if unexpected:
        log_git_action("diff_validation_failed", {
            "expected": expected_files,
            "unexpected": unexpected,
            "all_changed": changed,
        })
        return False, f"Unexpected files modified: {unexpected}"
    
    # Check diff size
    stats = get_diff_stats()
    if stats["total_lines"] > MAX_LINES_PER_COMMIT:
        return False, f"Diff too large: {stats['total_lines']} lines (max: {MAX_LINES_PER_COMMIT})"
    
    log_git_action("diff_validated", {
        "files": changed,
        "stats": stats,
    })
    return True, f"Valid: {len(changed)} files, {stats['total_lines']} lines"


def get_full_diff() -> str:
    """Get the full diff for review."""
    return _run("git diff", check=False)


def get_diff_summary() -> str:
    """Get a summary of changes (stat format)."""
    return _run("git diff --stat", check=False)


# ============================================================
# UPGRADE 3: Semantic Commits (Machine-Readable)
# ============================================================

SEMANTIC_PREFIXES = {
    "fix": "Bug fix",
    "feat": "New feature",
    "refactor": "Code refactoring",
    "test": "Test changes",
    "docs": "Documentation",
    "perf": "Performance improvement",
    "chore": "Maintenance",
    "style": "Code style",
    "security": "Security fix",
    "revert": "Revert previous commit",
}


def format_semantic_commit(prefix: str, scope: str, message: str) -> str:
    """
    Format a semantic commit message.
    
    Example: fix(runtime): handle None in tokenizer
    """
    if prefix not in SEMANTIC_PREFIXES:
        prefix = "chore"  # Default fallback
    
    scope = scope.replace(" ", "-").lower()
    message = message.strip()
    
    if scope:
        return f"{prefix}({scope}): {message}"
    return f"{prefix}: {message}"


def parse_semantic_commit(msg: str) -> dict:
    """Parse a semantic commit message into components."""
    import re
    pattern = r"^(\w+)(?:\(([^)]+)\))?: (.+)$"
    match = re.match(pattern, msg)
    
    if match:
        return {
            "prefix": match.group(1),
            "scope": match.group(2) or "",
            "message": match.group(3),
            "is_semantic": True,
        }
    return {
        "prefix": "unknown",
        "scope": "",
        "message": msg,
        "is_semantic": False,
    }


def commit_semantic(prefix: str, scope: str, message: str, files: Optional[List[str]] = None) -> Tuple[str, bool]:
    """
    Commit with a semantic message format.
    
    Args:
        prefix: fix, feat, refactor, test, etc.
        scope: Component being changed (e.g., runtime, auth, core)
        message: Brief description
        files: Files to stage (None = all)
    
    Returns:
        (commit_hash, success)
    """
    semantic_msg = format_semantic_commit(prefix, scope, message)
    return commit_patch(semantic_msg, files)


# ============================================================
# UPGRADE 4: Local Static Analysis Integration
# ============================================================

STATIC_ANALYZERS = {
    "flake8": {"cmd": "flake8 {file}", "purpose": "Logic + style bugs"},
    "mypy": {"cmd": "mypy {file} --ignore-missing-imports", "purpose": "Type correctness"},
    "bandit": {"cmd": "bandit -q {file}", "purpose": "Security bugs"},
}


def run_static_analysis(file_path: str) -> dict:
    """
    Run all local static analyzers on a file.
    
    Returns:
        {
            "passed": bool,
            "results": {tool: {passed, output}},
            "summary": str
        }
    """
    results = {}
    all_passed = True
    
    # Ensure we're using venv Python
    venv_python = str(ROOT / "venv" / "Scripts" / "python.exe")
    
    for tool, config in STATIC_ANALYZERS.items():
        cmd = config["cmd"].format(file=file_path)
        full_cmd = f"{venv_python} -m {cmd}"
        
        try:
            output = _run(full_cmd, check=False)
            # flake8/mypy/bandit return non-zero on issues
            result = subprocess.run(
                full_cmd,
                shell=True,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            passed = result.returncode == 0
            output = result.stdout + result.stderr
        except Exception as e:
            passed = False
            output = str(e)
        
        results[tool] = {
            "passed": passed,
            "output": output.strip()[:500],  # Limit output
            "purpose": config["purpose"],
        }
        
        if not passed:
            all_passed = False
    
    summary = "All checks passed" if all_passed else f"Failed: {[k for k,v in results.items() if not v['passed']]}"
    
    log_git_action("static_analysis", {
        "file": file_path,
        "passed": all_passed,
        "tools_run": list(results.keys()),
    })
    
    return {
        "passed": all_passed,
        "results": results,
        "summary": summary,
    }


def run_all_analysis(files: List[str]) -> dict:
    """Run static analysis on all changed files."""
    all_results = {}
    all_passed = True
    
    for f in files:
        if f.endswith(".py"):
            result = run_static_analysis(str(ROOT / f))
            all_results[f] = result
            if not result["passed"]:
                all_passed = False
    
    return {
        "passed": all_passed,
        "files_checked": len(all_results),
        "results": all_results,
    }


# ============================================================
# UPGRADE 5: Failure Memory via Git Tags
# ============================================================

def tag_failed_fix(reason: str, files: List[str] = None) -> str:
    """
    Tag a failed fix attempt for learning and audit.
    
    Creates: failed-fix-<short-hash>-<timestamp>
    """
    commit = get_current_commit()[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag_name = f"failed-fix-{commit}-{timestamp}"
    
    # Create annotated tag with details
    message = f"Failed fix attempt\nReason: {reason}\nFiles: {files or 'unknown'}"
    
    try:
        _run(f'git tag -a {tag_name} -m "{message}"')
        
        log_git_action("failure_tagged", {
            "tag": tag_name,
            "reason": reason,
            "files": files,
            "commit": commit,
        })
        
        return tag_name
    except Exception as e:
        return f"Failed to tag: {e}"


def get_failed_fixes() -> List[dict]:
    """Get all failed fix tags for learning."""
    try:
        output = _run("git tag -l 'failed-fix-*'", check=False)
        tags = [t.strip() for t in output.split("\n") if t.strip()]
        
        failures = []
        for tag in tags:
            try:
                msg = _run(f"git tag -l -n999 {tag}", check=False)
                failures.append({
                    "tag": tag,
                    "message": msg,
                })
            except:
                failures.append({"tag": tag, "message": ""})
        
        return failures
    except:
        return []


def has_similar_failure(file_path: str, issue_hash: str) -> bool:
    """
    Check if we've already failed on a similar issue.
    Helps avoid repeated failures.
    """
    failures = get_failed_fixes()
    file_name = Path(file_path).name
    
    for f in failures:
        msg = f.get("message", "")
        if file_name in msg or issue_hash in msg:
            log_git_action("similar_failure_found", {
                "file": file_path,
                "previous_tag": f["tag"],
            })
            return True
    
    return False


# ============================================================
# Enhanced get_status with all upgrades
# ============================================================

def get_enhanced_status() -> dict:
    """Get comprehensive git status with all upgrade info."""
    base = get_status()
    
    # Add failure history
    failures = get_failed_fixes()
    
    base.update({
        "failed_fix_count": len(failures),
        "recent_failures": failures[-5:] if failures else [],
        "semantic_prefixes": list(SEMANTIC_PREFIXES.keys()),
        "static_analyzers": list(STATIC_ANALYZERS.keys()),
        "upgrades_enabled": [
            "bisect",
            "diff_validation",
            "semantic_commits",
            "static_analysis",
            "failure_tagging",
        ],
    })
    
    return base
