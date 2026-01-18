# core/task_planner.py
"""
Task Planner - Converts natural language requests into executable task plans.
Integrates with TTS for plan preview announcements.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from core.llm_brain import llm_generate, load_prompt_template

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"


@dataclass
class TaskStep:
    type: str  # "generate_patch", "create_file", "run_test", "analyze", "refactor"
    file: str
    description: str
    priority: int = 1
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TaskPlan:
    goal: str
    steps: List[TaskStep]
    created_at: str
    model_used: str
    estimated_complexity: str  # "low", "medium", "high"


def create_plan(request: str) -> TaskPlan:
    """
    Convert a natural language request into a structured task plan.
    
    Args:
        request: Natural language description of what to do
        
    Returns:
        TaskPlan with executable steps
    """
    # Load planner prompt
    system_prompt = load_prompt_template("planner.system.txt")
    if not system_prompt:
        system_prompt = """You are a task planner for a code assistant. Convert user requests into executable plans.

Output a JSON object with:
{
  "goal": "summarized goal",
  "complexity": "low" | "medium" | "high",
  "steps": [
    {
      "type": "generate_patch" | "create_file" | "run_test" | "analyze" | "refactor",
      "file": "path/to/file.py",
      "description": "what to do",
      "priority": 1
    }
  ]
}

Rules:
1. Break down complex requests into small, atomic steps
2. Always include a test step after code changes
3. Order steps logically (analyze -> implement -> test)
4. For refactoring, limit scope to one file per step
5. Output ONLY valid JSON, no other text"""

    user_prompt = f"""Convert this request into an executable plan:

"{request}"

Output the JSON plan:"""

    response = llm_generate(
        prompt=user_prompt,
        model_hint="reason",
        system_prompt=system_prompt,
        max_tokens=1024,
        temperature=0.2,
    )
    
    # Parse response
    try:
        text = response.text
        if "`json" in text:
            match = re.search(r"`json\n(.*?)`", text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "`" in text:
            match = re.search(r"`\n?(.*?)`", text, re.DOTALL)
            if match:
                text = match.group(1)
        
        data = json.loads(text)
        
        steps = []
        for s in data.get("steps", []):
            steps.append(TaskStep(
                type=s.get("type", "analyze"),
                file=s.get("file", ""),
                description=s.get("description", ""),
                priority=s.get("priority", 1),
            ))
        
        return TaskPlan(
            goal=data.get("goal", request[:100]),
            steps=steps,
            created_at=datetime.now().isoformat(),
            model_used=response.model,
            estimated_complexity=data.get("complexity", "medium"),
        )
    except json.JSONDecodeError:
        # Fallback: create a simple analysis step
        return TaskPlan(
            goal=request[:100],
            steps=[TaskStep(
                type="analyze",
                file="",
                description=request,
                priority=1,
            )],
            created_at=datetime.now().isoformat(),
            model_used=response.model,
            estimated_complexity="unknown",
        )


def plan_preview(plan: TaskPlan, speak: bool = True) -> str:
    """
    Generate a human-readable preview of the plan.
    Optionally speak it via TTS.
    
    Args:
        plan: The task plan to preview
        speak: Whether to speak the preview via TTS
        
    Returns:
        Human-readable preview text
    """
    lines = [f"Plan: {plan.goal}"]
    lines.append(f"Complexity: {plan.estimated_complexity}")
    lines.append(f"Steps: {len(plan.steps)}")
    
    for i, step in enumerate(plan.steps, 1):
        lines.append(f"  {i}. [{step.type}] {step.description[:60]}")
        if step.file:
            lines.append(f"      File: {step.file}")
    
    preview_text = "\n".join(lines)
    
    # Generate spoken summary
    spoken_summary = f"I have a plan with {len(plan.steps)} steps. "
    if plan.estimated_complexity == "high":
        spoken_summary += "This is a complex task. "
    spoken_summary += f"Goal: {plan.goal[:50]}."
    
    if speak:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(spoken_summary)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Failed to speak: {e}")
    
    return preview_text


def execute_plan(plan: TaskPlan, dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute a task plan step by step.
    
    Args:
        plan: The plan to execute
        dry_run: If True, only simulate execution
        
    Returns:
        Dict with execution results
    """
    from core.autonomous_coder import analyze_and_fix, implement_feature
    
    results = {
        "goal": plan.goal,
        "steps_total": len(plan.steps),
        "steps_completed": 0,
        "steps_failed": 0,
        "files_changed": [],
        "success": True,
        "dry_run": dry_run,
    }
    
    for i, step in enumerate(plan.steps):
        print(f"[Planner] Executing step {i+1}/{len(plan.steps)}: {step.type}")
        
        if dry_run:
            print(f"  [DRY RUN] Would execute: {step.description}")
            results["steps_completed"] += 1
            continue
        
        if step.type == "analyze":
            # Just analyze, don't modify
            print(f"  Analyzing: {step.description}")
            results["steps_completed"] += 1
            
        elif step.type in ("generate_patch", "refactor"):
            # Use autonomous coder to fix/refactor
            fix_result = analyze_and_fix(f"{step.description} in {step.file}")
            if fix_result.success:
                results["steps_completed"] += 1
                results["files_changed"].extend(fix_result.files_changed)
            else:
                results["steps_failed"] += 1
                results["success"] = False
                print(f"  Step failed: {fix_result.message}")
                break
                
        elif step.type == "create_file":
            # Create new file
            fix_result = implement_feature(f"Create file {step.file}: {step.description}")
            if fix_result.success:
                results["steps_completed"] += 1
                results["files_changed"].extend(fix_result.files_changed)
            else:
                results["steps_failed"] += 1
                results["success"] = False
                break
                
        elif step.type == "run_test":
            # Run tests
            from core.autonomous_coder import run_tests
            passed, output = run_tests([step.file] if step.file else None)
            if passed:
                results["steps_completed"] += 1
            else:
                results["steps_failed"] += 1
                results["success"] = False
                print(f"  Tests failed: {output[:200]}")
                break
        else:
            # Unknown step type
            print(f"  Unknown step type: {step.type}")
            results["steps_completed"] += 1
    
    return results


def quick_command(command: str) -> Dict[str, Any]:
    """
    Handle quick voice commands that map to specific actions.
    
    Recognized commands:
    - "improve yourself" -> self-improvement analysis
    - "refactor [module]" -> refactor specified module
    - "fix [issue]" -> analyze and fix
    - "add feature [description]" -> implement feature
    """
    command_lower = command.lower().strip()
    
    # Command patterns
    if "improve yourself" in command_lower or "self improve" in command_lower:
        plan = create_plan("Analyze the codebase and suggest improvements to code quality, performance, or maintainability")
        return {"type": "plan", "plan": plan, "action": "self_improve"}
    
    elif command_lower.startswith("refactor"):
        target = command_lower.replace("refactor", "").strip()
        plan = create_plan(f"Refactor the {target} module to improve code quality")
        return {"type": "plan", "plan": plan, "action": "refactor"}
    
    elif command_lower.startswith("fix"):
        issue = command_lower.replace("fix", "").strip()
        return {"type": "fix", "issue": issue, "action": "analyze_and_fix"}
    
    elif "add feature" in command_lower:
        feature = command_lower.replace("add feature", "").strip()
        plan = create_plan(f"Implement new feature: {feature}")
        return {"type": "plan", "plan": plan, "action": "implement_feature"}
    
    elif "summarize" in command_lower or "digest" in command_lower:
        return {"type": "digest", "action": "generate_digest"}
    
    else:
        # Generic request - create a plan
        plan = create_plan(command)
        return {"type": "plan", "plan": plan, "action": "execute_plan"}


if __name__ == "__main__":
    print("=== Task Planner ===")
    print("Creating sample plan...\n")
    
    sample_request = "Add a feature to log all LLM responses to a file"
    plan = create_plan(sample_request)
    
    print(plan_preview(plan, speak=False))
    print(f"\nModel used: {plan.model_used}")
    print(f"Created at: {plan.created_at}")
