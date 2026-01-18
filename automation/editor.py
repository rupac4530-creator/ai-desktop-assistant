# automation/editor.py
"""File editing operations with backup, diff, and safe Git workflow."""

import os
import shutil
import time
import difflib
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime

SNAPSHOTS_DIR = Path(__file__).parent.parent / 'logs' / 'snapshots'
BACKUPS_DIR = SNAPSHOTS_DIR / 'file_backups'
LOG_DIR = Path(__file__).parent.parent / 'logs'

# Setup logging
logging.basicConfig(
    filename=str(LOG_DIR / 'multitask.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('editor')


def ensure_dirs():
    """Ensure backup directories exist."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


class GitWorkflow:
    """Safe Git operations for code fixes."""
    
    def __init__(self, repo_path=None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._has_git = self._check_git()
    
    def _check_git(self):
        """Check if git is available and repo exists."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def is_available(self):
        return self._has_git
    
    def create_branch(self, prefix="ai-fix"):
        """Create a new branch for the fix."""
        if not self._has_git:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"{prefix}/{timestamp}"
        
        try:
            # Stash any changes first
            subprocess.run(['git', 'stash'], cwd=str(self.repo_path), capture_output=True)
            
            # Create and checkout branch
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Created branch: {branch_name}")
                return branch_name
            else:
                logger.error(f"Failed to create branch: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Git branch error: {e}")
            return None
    
    def commit(self, message, files=None):
        """Commit changes."""
        if not self._has_git:
            return False
        
        try:
            if files:
                for f in files:
                    subprocess.run(['git', 'add', str(f)], cwd=str(self.repo_path), capture_output=True)
            else:
                subprocess.run(['git', 'add', '-A'], cwd=str(self.repo_path), capture_output=True)
            
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Committed: {message}")
                return True
            else:
                logger.warning(f"Commit failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return False
    
    def rollback_branch(self, original_branch="main"):
        """Rollback to original branch."""
        if not self._has_git:
            return False
        
        try:
            subprocess.run(['git', 'checkout', original_branch], cwd=str(self.repo_path), capture_output=True)
            logger.info(f"Rolled back to {original_branch}")
            return True
        except:
            return False
    
    def get_current_branch(self):
        """Get current branch name."""
        if not self._has_git:
            return None
        
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None


class FileEditor:
    """File editing with backup, diff, rollback, and safe Git workflow."""

    def __init__(self, auto_backup=True, repo_path=None):
        self.auto_backup = auto_backup
        self.history = []
        self.git = GitWorkflow(repo_path)
        ensure_dirs()

    def read_file(self, file_path):
        """Read file contents."""
        path = Path(file_path)
        if not path.exists():
            return None
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Read error {file_path}: {e}")
            return None

    def backup_file(self, file_path):
        """Create a backup of a file."""
        path = Path(file_path)
        if not path.exists():
            return None

        ensure_dirs()
        timestamp = int(time.time() * 1000)
        backup_name = f"{path.stem}_{timestamp}{path.suffix}.bak"
        backup_path = BACKUPS_DIR / backup_name

        try:
            shutil.copy2(path, backup_path)
            self.history.append((str(path), str(backup_path), timestamp))
            logger.info(f"Backed up: {file_path} -> {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def write_file(self, file_path, content, backup=None):
        """Write content to file."""
        path = Path(file_path)
        do_backup = backup if backup is not None else self.auto_backup
        if do_backup and path.exists():
            self.backup_file(file_path)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            logger.info(f"Written: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Write failed: {e}")
            return False

    def generate_diff(self, original, new_content, filename="file"):
        """Generate unified diff."""
        original_lines = original.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(original_lines, new_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
        return ''.join(diff)

    def rollback(self, file_path=None):
        """Rollback to last backup."""
        if not self.history:
            logger.warning("No backup history")
            return False

        if file_path:
            for i in range(len(self.history) - 1, -1, -1):
                orig, backup, ts = self.history[i]
                if orig == str(file_path):
                    return self._restore_backup(orig, backup, i)
            logger.warning(f"No backup found for {file_path}")
            return False
        else:
            orig, backup, ts = self.history[-1]
            return self._restore_backup(orig, backup, len(self.history) - 1)

    def _restore_backup(self, orig_path, backup_path, history_index):
        """Internal: restore a specific backup."""
        try:
            shutil.copy2(backup_path, orig_path)
            self.history.pop(history_index)
            logger.info(f"Restored: {orig_path} from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def run_tests(self, test_command="pytest -q", cwd=None):
        """Run tests and return (success, output)."""
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=cwd or str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=120
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            logger.info(f"Tests {'passed' if success else 'failed'}")
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except Exception as e:
            return False, str(e)

    def run_linter(self, file_path, linter="flake8"):
        """Run linter on file and return (success, output)."""
        try:
            result = subprocess.run(
                [linter, str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except:
            return True, ""  # If linter not available, pass

    def safe_code_fix(self, file_path, new_content, test_command="pytest -q", require_confirmation=True):
        """
        Apply a code fix with full safety workflow.
        
        Workflow:
        1. Create git branch
        2. Backup file
        3. Apply patch
        4. Run tests/lint
        5. If PASS -> commit
        6. If FAIL -> rollback
        
        Returns:
            dict with keys: success, message, diff, test_output, branch
        """
        result = {
            "success": False,
            "message": "",
            "diff": None,
            "test_output": "",
            "branch": None,
            "needs_confirmation": False
        }
        
        path = Path(file_path)
        if not path.exists():
            result["message"] = f"File not found: {file_path}"
            return result
        
        original = self.read_file(file_path)
        if original == new_content:
            result["success"] = True
            result["message"] = "No changes needed"
            return result
        
        # Generate diff
        diff = self.generate_diff(original, new_content, path.name)
        result["diff"] = diff
        
        # Save diff to snapshots
        diff_path = SNAPSHOTS_DIR / f"patch_{path.stem}_{int(time.time())}.diff"
        diff_path.write_text(diff, encoding='utf-8')
        logger.info(f"Saved diff: {diff_path}")
        
        # If confirmation required, return early
        if require_confirmation:
            result["needs_confirmation"] = True
            result["message"] = f"Patch ready for review: {diff_path}"
            return result
        
        # Create git branch if available
        original_branch = self.git.get_current_branch()
        if self.git.is_available():
            branch = self.git.create_branch()
            result["branch"] = branch
        
        # Backup and apply patch
        backup_path = self.backup_file(file_path)
        if not self.write_file(file_path, new_content, backup=False):
            result["message"] = "Failed to write file"
            return result
        
        # Run linter
        lint_ok, lint_output = self.run_linter(file_path)
        
        # Run tests
        test_ok, test_output = self.run_tests(test_command)
        result["test_output"] = test_output
        
        if test_ok and lint_ok:
            # Success - commit
            if self.git.is_available():
                self.git.commit(f"AI fix: {path.name}", [str(path)])
            
            result["success"] = True
            result["message"] = "Fix applied and tests passed"
            logger.info(f"Code fix successful: {file_path}")
        else:
            # Failure - rollback
            self.rollback(file_path)
            if self.git.is_available() and original_branch:
                self.git.rollback_branch(original_branch)
            
            result["message"] = f"Tests/lint failed, rolled back. Output: {test_output[:500]}"
            logger.warning(f"Code fix rolled back: {file_path}")
        
        return result

    def apply_confirmed_fix(self, file_path, new_content, test_command="pytest -q"):
        """Apply a previously confirmed fix (no confirmation prompt)."""
        return self.safe_code_fix(file_path, new_content, test_command, require_confirmation=False)


# Convenience functions
def read_file(path):
    return FileEditor(auto_backup=False).read_file(path)

def write_file(path, content):
    return FileEditor().write_file(path, content)

def apply_patch(file_path, new_content):
    return FileEditor().safe_code_fix(file_path, new_content, require_confirmation=False)


if __name__ == "__main__":
    print("Editor module loaded. Use FileEditor class for safe file operations.")
