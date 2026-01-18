# core/model_selector.py
"""
Model Selector - Picks heavy vs light models based on DEVICE and available VRAM.
Implements resource-aware model routing for the autonomous brain.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Model registry with resource requirements
MODEL_REGISTRY = {
    # Code models (primary to fallback order)
    "code": [
        {"name": "codellama:7b-instruct", "vram_mb": 4500, "purpose": "code_refactor"},
        {"name": "starcoder2:3b", "vram_mb": 2000, "purpose": "code_generation"},
        {"name": "llama3:latest", "vram_mb": 5000, "purpose": "code_fallback"},
    ],
    # Reasoning models
    "reason": [
        {"name": "mistral:7b-instruct", "vram_mb": 4500, "purpose": "planning"},
        {"name": "llama3:latest", "vram_mb": 5000, "purpose": "reasoning_fallback"},
    ],
    # Summary/light models
    "summary": [
        {"name": "starcoder2:3b", "vram_mb": 2000, "purpose": "quick_summary"},
        {"name": "llama3:latest", "vram_mb": 5000, "purpose": "summary_fallback"},
    ],
    # General instruction following
    "general": [
        {"name": "llama3:latest", "vram_mb": 5000, "purpose": "general"},
        {"name": "mistral:7b-instruct", "vram_mb": 4500, "purpose": "general_fallback"},
    ],
}

# Cache for VRAM detection
_vram_cache: Optional[int] = None


def get_available_vram() -> int:
    """Get available VRAM in MB. Returns 0 if no GPU."""
    global _vram_cache
    if _vram_cache is not None:
        return _vram_cache

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            _vram_cache = int(result.stdout.strip().split("\n")[0])
            return _vram_cache
    except Exception:
        pass

    _vram_cache = 0
    return 0


def get_total_vram() -> int:
    """Get total VRAM in MB. Returns 0 if no GPU."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return int(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return 0


def get_device() -> str:
    """Get device from env or detect."""
    device = os.getenv("DEVICE", "").lower()
    if device in ("cuda", "gpu"):
        return "cuda"
    if device == "cpu":
        return "cpu"
    # Auto-detect
    return "cuda" if get_total_vram() > 0 else "cpu"


def select_model(hint: str, require_vram: bool = True) -> Tuple[str, Dict]:
    """
    Select best available model for the given hint.
    
    Args:
        hint: One of 'code', 'reason', 'summary', 'general'
        require_vram: If True, check VRAM availability
        
    Returns:
        Tuple of (model_name, model_info)
    """
    if hint not in MODEL_REGISTRY:
        hint = "general"

    candidates = MODEL_REGISTRY[hint]
    device = get_device()

    if device == "cpu" or not require_vram:
        # On CPU, pick smallest model
        candidates = sorted(candidates, key=lambda m: m["vram_mb"])
        return candidates[0]["name"], candidates[0]

    # On GPU, pick best model that fits
    available = get_available_vram()
    for model in candidates:
        if model["vram_mb"] <= available + 500:  # 500MB headroom
            return model["name"], model

    # Fallback to smallest
    candidates = sorted(candidates, key=lambda m: m["vram_mb"])
    return candidates[0]["name"], candidates[0]


def get_model_for_task(task_type: str) -> str:
    """
    Get model name for a specific task type.
    
    Task types:
        - code_fix: Fix bugs in code
        - code_refactor: Refactor/improve code
        - planning: Create execution plans
        - analysis: Analyze issues
        - summary: Quick summaries
    """
    task_to_hint = {
        "code_fix": "code",
        "code_refactor": "code",
        "code_generate": "code",
        "planning": "reason",
        "analysis": "reason",
        "summary": "summary",
        "explain": "reason",
        "general": "general",
    }
    hint = task_to_hint.get(task_type, "general")
    model_name, _ = select_model(hint)
    return model_name


def get_resource_summary() -> Dict:
    """Get current resource status."""
    return {
        "device": get_device(),
        "total_vram_mb": get_total_vram(),
        "available_vram_mb": get_available_vram(),
        "preferred_code_model": select_model("code")[0],
        "preferred_reason_model": select_model("reason")[0],
    }


if __name__ == "__main__":
    import json
    print("=== Model Selector Status ===")
    print(json.dumps(get_resource_summary(), indent=2))
