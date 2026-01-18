# core/llm_brain.py
"""
LLM Brain - The autonomous reasoning and code generation engine.
Uses Ollama as the primary runtime with model routing based on task type.
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import ollama
from dotenv import load_dotenv

from core.model_selector import select_model, get_model_for_task, get_device

load_dotenv(Path(__file__).parent.parent / ".env")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "core" / "prompts"
LOGS_DIR = PROJECT_ROOT / "logs"
PATCH_LOG = LOGS_DIR / "autonomous_patch_log.jsonl"

# Rate limiting
MAX_PATCHES_PER_HOUR = 3
_patch_timestamps: List[datetime] = []

# Ollama client
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@dataclass
class LLMResponse:
    text: str
    tokens: int
    model: str
    duration_ms: float
    usage: Dict[str, Any]


def load_prompt_template(name: str) -> str:
    """Load a prompt template from core/prompts/"""
    path = PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def llm_generate(
    prompt: str,
    model_hint: str = "general",
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    stream: bool = False,
) -> LLMResponse:
    """
    Generate text using the LLM.
    
    Args:
        prompt: User prompt
        model_hint: One of 'code', 'reason', 'summary', 'general'
        system_prompt: Optional system prompt override
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        stream: Whether to stream response
        
    Returns:
        LLMResponse with generated text and metadata
    """
    model_name, model_info = select_model(model_hint)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    start = time.time()
    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            options={
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        )
        duration_ms = (time.time() - start) * 1000
        
        return LLMResponse(
            text=response["message"]["content"],
            tokens=response.get("eval_count", 0),
            model=model_name,
            duration_ms=duration_ms,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_duration": response.get("total_duration", 0),
            },
        )
    except Exception as e:
        return LLMResponse(
            text=f"ERROR: {e}",
            tokens=0,
            model=model_name,
            duration_ms=(time.time() - start) * 1000,
            usage={"error": str(e)},
        )


def generate_code_patch(
    context_files: Dict[str, str],
    target_file: str,
    instruction: str,
    max_lines: int = 500,
) -> Dict[str, Any]:
    """
    Generate a unified diff patch for the target file.
    
    Args:
        context_files: Dict of {filepath: content} for context
        target_file: Path to the file to modify
        instruction: What change to make
        max_lines: Maximum patch size
        
    Returns:
        Dict with 'patch', 'explanation', 'model', 'success'
    """
    # Check rate limit
    now = datetime.now()
    global _patch_timestamps
    _patch_timestamps = [t for t in _patch_timestamps if (now - t).seconds < 3600]
    if len(_patch_timestamps) >= MAX_PATCHES_PER_HOUR:
        return {
            "patch": "",
            "explanation": "Rate limit exceeded (3 patches/hour)",
            "model": "",
            "success": False,
            "rate_limited": True,
        }
    
    # Load system prompt
    system_prompt = load_prompt_template("code_fix.system.txt")
    if not system_prompt:
        system_prompt = '''You are an expert code assistant. Generate ONLY a unified diff patch.
Rules:
1. Change ONLY what is necessary to fix the issue
2. Preserve existing code style and formatting
3. Do not add unnecessary comments
4. Output ONLY the unified diff, nothing else
5. Use proper diff format: --- a/file, +++ b/file, @@ line numbers @@'''

    # Build context
    context_text = ""
    for fpath, content in context_files.items():
        context_text += f"=== {fpath} ===\n{content}\n\n"
    
    target_content = context_files.get(target_file, "")
    
    user_prompt = f"""Context files:
{context_text}

Target file to modify: {target_file}
Current content:
`
{target_content}
`

Instruction: {instruction}

Generate a unified diff patch to accomplish this. Output ONLY the diff, no explanation."""

    response = llm_generate(
        prompt=user_prompt,
        model_hint="code",
        system_prompt=system_prompt,
        max_tokens=2048,
        temperature=0.1,
    )
    
    # Extract diff from response
    patch_text = response.text
    # Try to extract code block if present
    if "`diff" in patch_text:
        match = re.search(r"`diff\n(.*?)`", patch_text, re.DOTALL)
        if match:
            patch_text = match.group(1)
    elif "`" in patch_text:
        match = re.search(r"`\n?(.*?)`", patch_text, re.DOTALL)
        if match:
            patch_text = match.group(1)
    
    # Check patch size
    lines = patch_text.strip().split("\n")
    if len(lines) > max_lines:
        return {
            "patch": "",
            "explanation": f"Patch too large ({len(lines)} lines > {max_lines})",
            "model": response.model,
            "success": False,
            "too_large": True,
        }
    
    _patch_timestamps.append(now)
    
    return {
        "patch": patch_text.strip(),
        "explanation": "",
        "model": response.model,
        "success": True,
        "tokens": response.tokens,
    }


def explain_change(patch: str) -> str:
    """
    Generate a human-readable explanation of a patch.
    
    Args:
        patch: Unified diff text
        
    Returns:
        Human-readable explanation
    """
    system_prompt = """You are a code reviewer. Explain what this patch does in 1-2 sentences.
Be concise and focus on the functional change, not the mechanics."""

    response = llm_generate(
        prompt=f"Explain this patch:\n\n{patch}",
        model_hint="summary",
        system_prompt=system_prompt,
        max_tokens=256,
        temperature=0.3,
    )
    
    return response.text.strip()


def analyze_error(
    error_text: str,
    file_contents: Dict[str, str],
) -> Dict[str, Any]:
    """
    Analyze an error and suggest a fix.
    
    Args:
        error_text: Error message / stack trace
        file_contents: Relevant file contents
        
    Returns:
        Dict with 'analysis', 'suggested_fix', 'target_file', 'confidence'
    """
    system_prompt = """You are a debugging expert. Analyze the error and suggest a fix.
Output JSON with:
{
  "analysis": "what went wrong",
  "suggested_fix": "how to fix it",
  "target_file": "file to modify",
  "confidence": 0.0-1.0
}"""

    context = ""
    for fpath, content in file_contents.items():
        context += f"=== {fpath} ===\n{content[:2000]}\n\n"

    response = llm_generate(
        prompt=f"Error:\n{error_text}\n\nRelevant files:\n{context}",
        model_hint="reason",
        system_prompt=system_prompt,
        max_tokens=1024,
        temperature=0.2,
    )
    
    try:
        # Try to parse JSON from response
        text = response.text
        if "`json" in text:
            match = re.search(r"`json\n(.*?)`", text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "`" in text:
            match = re.search(r"`\n?(.*?)`", text, re.DOTALL)
            if match:
                text = match.group(1)
        
        result = json.loads(text)
        result["model"] = response.model
        return result
    except json.JSONDecodeError:
        return {
            "analysis": response.text,
            "suggested_fix": "",
            "target_file": "",
            "confidence": 0.3,
            "model": response.model,
        }


def log_patch_action(
    action: str,
    patch_files: List[str],
    tests_result: str,
    model_used: str,
    explanation: str,
    commit_before: str = "",
    commit_after: str = "",
    rollback: bool = False,
):
    """Log a patch action to the audit trail."""
    LOGS_DIR.mkdir(exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "patch_files": patch_files,
        "tests_run": True,
        "tests_result": tests_result,
        "rollback_flag": rollback,
        "explanation_text": explanation,
        "llm_model_used": model_used,
        "commit_before": commit_before,
        "commit_after": commit_after,
    }
    
    with open(PATCH_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_brain_status() -> Dict[str, Any]:
    """Get current brain status."""
    return {
        "device": get_device(),
        "ollama_url": OLLAMA_BASE_URL,
        "code_model": select_model("code")[0],
        "reason_model": select_model("reason")[0],
        "patches_this_hour": len(_patch_timestamps),
        "max_patches_per_hour": MAX_PATCHES_PER_HOUR,
        "prompts_dir": str(PROMPTS_DIR),
    }


if __name__ == "__main__":
    print("=== LLM Brain Status ===")
    print(json.dumps(get_brain_status(), indent=2))
    
    # Quick test
    print("\n=== Quick Generation Test ===")
    resp = llm_generate("Say 'Hello, I am your autonomous brain.' in one line.", model_hint="general")
    print(f"Response: {resp.text}")
    print(f"Model: {resp.model}")
    print(f"Tokens: {resp.tokens}")
