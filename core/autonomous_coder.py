# core/autonomous_coder.py
"""
Autonomous Coder - Analyzes issues and generates fixes autonomously.
Implements the test-first, snapshot, apply, rollback cycle.
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from core.llm_brain import (
    llm_generate,
    generate_code_patch,
    explain_change,
    analyze_error,
    log_patch_action,
)
from core.model_selector import get_model_for_task

# Git integration
try:
    from core.git_helper import (
        snapshot_repo as git_snapshot,
        start_autobranch,
        commit_patch as git_commit,
        merge_branch,
        rollback_to,
        get_current_commit,
        log_git_action,
        is_git_repo,
    )
    GIT_ENABLED = is_git_repo()
except ImportError:
    GIT_ENABLED = False

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
SNAPSHOTS_DIR = LOGS_DIR / "snapshots"
FAIL_LOG = LOGS_DIR / "self_update_fail.log"

# Safety limits
MAX_PATCH_LINES = 500
MAX_RETRIES = 2


@dataclass
class FixResult:
    success: bool
    message: str
    patch_applied: bool
    tests_passed: bool
    files_changed: List[str]
    rollback_performed: bool
    explanation: str
    model_used: str


def create_snapshot(label: str) -> Path:
    """Create a snapshot before applying changes."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = SNAPSHOTS_DIR / f"{ts}_{label}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy critical files
    files_to_backup = [
        ".env",
        "core/main_controller.py",
        "core/llm_brain.py",
        "core/autonomous_coder.py",
        "core/repair_engine.py",
        "core/self_update.py",
        "speech/asr.py",
        "speech/local_tts.py",
    ]
    
    for f in files_to_backup:
        src = PROJECT_ROOT / f
        if src.exists():
            dst = snapshot_dir / f.replace("/", "_")
            shutil.copy2(src, dst)
    
    return snapshot_dir


def restore_snapshot(snapshot_dir: Path) -> bool:
    """Restore files from a snapshot."""
    if not snapshot_dir.exists():
        return False
    
    for backup_file in snapshot_dir.iterdir():
        if backup_file.is_file():
            # Convert back to original path
            original_name = backup_file.name.replace("_", "/", 1)
            # Handle special case for .env
            if backup_file.name == ".env":
                original_name = ".env"
            dst = PROJECT_ROOT / original_name
            if dst.parent.exists():
                shutil.copy2(backup_file, dst)
    
    return True


def run_tests(test_files: Optional[List[str]] = None) -> Tuple[bool, str]:
    """Run pytest and return (passed, output)."""
    if test_files is None:
        test_files = [
            "tools/test_core_smoke.py",
        ]
    
    cmd = [
        str(PROJECT_ROOT / "venv" / "Scripts" / "python.exe"),
        "-m", "pytest", "-q", "--tb=short"
    ] + test_files
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Tests timed out"
    except Exception as e:
        return False, f"Test error: {e}"


def apply_patch(patch_text: str, target_file: str) -> Tuple[bool, str]:
    """
    Apply a unified diff patch to a file.
    Returns (success, message).
    """
    target_path = PROJECT_ROOT / target_file
    if not target_path.exists():
        return False, f"Target file not found: {target_file}"
    
    # For simple patches, we parse and apply manually
    # This is a simplified implementation
    try:
        original = target_path.read_text(encoding="utf-8")
        lines = original.split("\n")
        
        # Parse the patch (simplified - handles basic unified diff)
        patch_lines = patch_text.strip().split("\n")
        
        # Find hunks
        new_lines = lines.copy()
        offset = 0
        
        i = 0
        while i < len(patch_lines):
            line = patch_lines[i]
            if line.startswith("@@"):
                # Parse hunk header: @@ -start,count +start,count @@
                match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    old_start = int(match.group(1)) - 1 + offset
                    
                    # Process hunk lines
                    i += 1
                    deletions = []
                    additions = []
                    
                    while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
                        hunk_line = patch_lines[i]
                        if hunk_line.startswith("-") and not hunk_line.startswith("---"):
                            deletions.append(hunk_line[1:])
                        elif hunk_line.startswith("+") and not hunk_line.startswith("+++"):
                            additions.append(hunk_line[1:])
                        elif hunk_line.startswith(" "):
                            pass  # Context line
                        i += 1
                    
                    # Apply: remove deletions, add additions
                    if deletions:
                        for del_line in deletions:
                            for j, existing in enumerate(new_lines):
                                if existing.strip() == del_line.strip():
                                    new_lines.pop(j)
                                    offset -= 1
                                    break
                    
                    if additions:
                        insert_pos = old_start
                        for add_line in additions:
                            new_lines.insert(insert_pos, add_line)
                            insert_pos += 1
                            offset += 1
                    
                    continue
            i += 1
        
        # Write the patched file
        target_path.write_text("\n".join(new_lines), encoding="utf-8")
        return True, "Patch applied"
        
    except Exception as e:
        return False, f"Patch failed: {e}"


def revert_file(target_file: str, snapshot_dir: Path) -> bool:
    """Revert a file from snapshot."""
    backup_name = target_file.replace("/", "_")
    backup_path = snapshot_dir / backup_name
    
    if backup_path.exists():
        target_path = PROJECT_ROOT / target_file
        shutil.copy2(backup_path, target_path)
        return True
    return False


def find_relevant_files(issue_description: str) -> Dict[str, str]:
    """
    Find files relevant to an issue based on keywords.
    Returns dict of {filepath: content}.
    """
    files = {}
    
    # Keywords to file mapping
    keyword_files = {
        "tts": ["speech/local_tts.py"],
        "speech": ["speech/asr.py", "speech/local_tts.py"],
        "asr": ["speech/asr.py"],
        "whisper": ["speech/asr.py"],
        "keyboard": ["ui/keyboard.py"],
        "hotkey": ["ui/keyboard.py"],
        "ptt": ["ui/keyboard.py", "core/main_controller.py"],
        "avatar": ["integrations/avatar.py"],
        "vtube": ["integrations/avatar.py"],
        "browser": ["automation/browser_action.py"],
        "llm": ["core/llm_brain.py"],
        "self-heal": ["core/watchdog.py", "core/repair_engine.py"],
        "update": ["core/self_update.py"],
        "main": ["core/main_controller.py"],
    }
    
    issue_lower = issue_description.lower()
    
    for keyword, filepaths in keyword_files.items():
        if keyword in issue_lower:
            for fp in filepaths:
                path = PROJECT_ROOT / fp
                if path.exists():
                    try:
                        files[fp] = path.read_text(encoding="utf-8")
                    except:
                        pass
    
    # Always include main_controller if nothing found
    if not files:
        main = PROJECT_ROOT / "core/main_controller.py"
        if main.exists():
            files["core/main_controller.py"] = main.read_text(encoding="utf-8")
    
    return files


def analyze_and_fix(issue_description: str) -> FixResult:
    """
    Analyze an issue and attempt to fix it autonomously.
    
    Steps:
    1. Find relevant files
    2. Analyze the issue with LLM
    3. Generate a patch
    4. Create snapshot
    5. Apply patch
    6. Run tests
    7. If tests pass -> commit, if fail -> rollback
    """
    print(f"[AutoCoder] Analyzing issue: {issue_description[:100]}...")
    
    # Step 1: Find relevant files
    context_files = find_relevant_files(issue_description)
    if not context_files:
        return FixResult(
            success=False,
            message="No relevant files found",
            patch_applied=False,
            tests_passed=False,
            files_changed=[],
            rollback_performed=False,
            explanation="",
            model_used="",
        )
    
    # Step 2: Analyze the issue
    analysis = analyze_error(issue_description, context_files)
    target_file = analysis.get("target_file", "")
    confidence = analysis.get("confidence", 0)
    
    if not target_file or confidence < 0.5:
        # Try to infer target from context
        target_file = list(context_files.keys())[0]
    
    print(f"[AutoCoder] Analysis: {analysis.get('analysis', '')[:100]}")
    print(f"[AutoCoder] Target file: {target_file}, Confidence: {confidence}")
    
    # Step 3: Generate patch
    patch_result = generate_code_patch(
        context_files=context_files,
        target_file=target_file,
        instruction=f"{issue_description}\n\nSuggested fix: {analysis.get('suggested_fix', '')}",
        max_lines=MAX_PATCH_LINES,
    )
    
    if not patch_result.get("success"):
        return FixResult(
            success=False,
            message=patch_result.get("explanation", "Patch generation failed"),
            patch_applied=False,
            tests_passed=False,
            files_changed=[],
            rollback_performed=False,
            explanation="",
            model_used=patch_result.get("model", ""),
        )
    
    patch_text = patch_result["patch"]
    model_used = patch_result["model"]
    
    # Generate explanation
    explanation = explain_change(patch_text)
    print(f"[AutoCoder] Patch explanation: {explanation}")
    
    # Step 4: Create snapshot
    snapshot_dir = create_snapshot("autofix")
    print(f"[AutoCoder] Created snapshot: {snapshot_dir}")
    
    # Step 5: Apply patch
    applied, apply_msg = apply_patch(patch_text, target_file)
    if not applied:
        return FixResult(
            success=False,
            message=f"Patch application failed: {apply_msg}",
            patch_applied=False,
            tests_passed=False,
            files_changed=[],
            rollback_performed=False,
            explanation=explanation,
            model_used=model_used,
        )
    
    print(f"[AutoCoder] Patch applied to {target_file}")
    
    # Step 6: Run tests
    tests_passed, test_output = run_tests()
    print(f"[AutoCoder] Tests passed: {tests_passed}")
    
    if tests_passed:
        # Success - log and return
        log_patch_action(
            action="autofix",
            patch_files=[target_file],
            tests_result="PASSED",
            model_used=model_used,
            explanation=explanation,
        )
        
        return FixResult(
            success=True,
            message="Fix applied successfully",
            patch_applied=True,
            tests_passed=True,
            files_changed=[target_file],
            rollback_performed=False,
            explanation=explanation,
            model_used=model_used,
        )
    else:
        # Step 7: Rollback on test failure
        print(f"[AutoCoder] Tests failed, rolling back...")
        revert_file(target_file, snapshot_dir)
        
        # Log failure
        log_patch_action(
            action="autofix_rollback",
            patch_files=[target_file],
            tests_result="FAILED",
            model_used=model_used,
            explanation=f"Rollback: {test_output[:500]}",
            rollback=True,
        )
        
        # Write to fail log
        with open(FAIL_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n=== {datetime.now().isoformat()} ===\n")
            f.write(f"Issue: {issue_description}\n")
            f.write(f"Patch:\n{patch_text}\n")
            f.write(f"Test output:\n{test_output}\n")
        
        return FixResult(
            success=False,
            message="Tests failed after patch, rolled back",
            patch_applied=True,
            tests_passed=False,
            files_changed=[target_file],
            rollback_performed=True,
            explanation=explanation,
            model_used=model_used,
        )


def implement_feature(feature_description: str) -> FixResult:
    """
    Implement a new feature by creating a plan and executing it.
    
    This is a higher-level function that:
    1. Creates a JSON plan of steps
    2. Executes each step with test validation
    3. Rolls back on failure
    """
    print(f"[AutoCoder] Planning feature: {feature_description[:100]}...")
    
    # Generate plan using reasoning model
    plan_prompt = f"""Create a step-by-step implementation plan for this feature:

{feature_description}

Output a JSON array of steps. Each step should have:
- "type": one of "create_file", "modify_file", "add_test"
- "file": the file path
- "description": what to do

Example:
[
  {{"type": "add_test", "file": "tools/test_new_feature.py", "description": "Add test for new feature"}},
  {{"type": "modify_file", "file": "core/some_module.py", "description": "Add the feature logic"}}
]

Output ONLY the JSON array, no other text."""

    response = llm_generate(
        prompt=plan_prompt,
        model_hint="reason",
        max_tokens=1024,
        temperature=0.2,
    )
    
    # Parse plan
    try:
        plan_text = response.text
        if "`json" in plan_text:
            match = re.search(r"`json\n(.*?)`", plan_text, re.DOTALL)
            if match:
                plan_text = match.group(1)
        elif "`" in plan_text:
            match = re.search(r"`\n?(.*?)`", plan_text, re.DOTALL)
            if match:
                plan_text = match.group(1)
        
        steps = json.loads(plan_text)
    except json.JSONDecodeError:
        return FixResult(
            success=False,
            message="Failed to parse implementation plan",
            patch_applied=False,
            tests_passed=False,
            files_changed=[],
            rollback_performed=False,
            explanation=response.text[:200],
            model_used=response.model,
        )
    
    print(f"[AutoCoder] Plan has {len(steps)} steps")
    
    # Create snapshot before any changes
    snapshot_dir = create_snapshot("feature")
    files_changed = []
    
    # Execute each step
    for i, step in enumerate(steps):
        step_type = step.get("type", "")
        step_file = step.get("file", "")
        step_desc = step.get("description", "")
        
        print(f"[AutoCoder] Step {i+1}/{len(steps)}: {step_type} - {step_file}")
        
        if step_type in ("modify_file", "create_file"):
            # Get current content if exists
            file_path = PROJECT_ROOT / step_file
            current_content = ""
            if file_path.exists():
                current_content = file_path.read_text(encoding="utf-8")
            
            # Generate the change
            if step_type == "create_file":
                # Generate new file content
                create_prompt = f"Create a Python file for: {step_desc}\n\nOutput ONLY the file content, no markdown."
                file_response = llm_generate(create_prompt, model_hint="code")
                new_content = file_response.text
                if "`python" in new_content:
                    match = re.search(r"`python\n(.*?)`", new_content, re.DOTALL)
                    if match:
                        new_content = match.group(1)
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(new_content, encoding="utf-8")
                files_changed.append(step_file)
            else:
                # Modify existing file
                result = analyze_and_fix(f"{step_desc} in file {step_file}")
                if result.success:
                    files_changed.extend(result.files_changed)
                else:
                    # Rollback all changes
                    restore_snapshot(snapshot_dir)
                    return FixResult(
                        success=False,
                        message=f"Step {i+1} failed: {result.message}",
                        patch_applied=False,
                        tests_passed=False,
                        files_changed=[],
                        rollback_performed=True,
                        explanation="",
                        model_used="",
                    )
    
    # Run final tests
    tests_passed, test_output = run_tests()
    
    if tests_passed:
        log_patch_action(
            action="implement_feature",
            patch_files=files_changed,
            tests_result="PASSED",
            model_used=response.model,
            explanation=feature_description[:200],
        )
        
        return FixResult(
            success=True,
            message="Feature implemented successfully",
            patch_applied=True,
            tests_passed=True,
            files_changed=files_changed,
            rollback_performed=False,
            explanation=feature_description,
            model_used=response.model,
        )
    else:
        # Rollback
        restore_snapshot(snapshot_dir)
        
        return FixResult(
            success=False,
            message="Final tests failed, rolled back all changes",
            patch_applied=True,
            tests_passed=False,
            files_changed=files_changed,
            rollback_performed=True,
            explanation=test_output[:500],
            model_used=response.model,
        )


if __name__ == "__main__":
    print("=== Autonomous Coder ===")
    print("Ready to analyze and fix issues.")
    print("\nUsage:")
    print("  from core.autonomous_coder import analyze_and_fix, implement_feature")
    print("  result = analyze_and_fix('Description of the issue')")
    print("  result = implement_feature('Description of new feature')")




