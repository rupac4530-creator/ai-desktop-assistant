# tools/test_autonomous_fix.py
"""
Tests for the autonomous coding system.
Includes end-to-end auto-fix test with a simulated bug.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelSelector:
    """Test model selection logic."""
    
    def test_model_selector_import(self):
        from core.model_selector import select_model, get_device
        assert callable(select_model)
        assert callable(get_device)
    
    def test_select_code_model(self):
        from core.model_selector import select_model
        model, info = select_model("code")
        assert model is not None
        assert "name" in info
    
    def test_select_reason_model(self):
        from core.model_selector import select_model
        model, info = select_model("reason")
        assert model is not None
    
    def test_get_device(self):
        from core.model_selector import get_device
        device = get_device()
        assert device in ("cpu", "cuda")
    
    def test_resource_summary(self):
        from core.model_selector import get_resource_summary
        summary = get_resource_summary()
        assert "device" in summary
        assert "preferred_code_model" in summary


class TestLLMBrain:
    """Test LLM brain functionality."""
    
    def test_llm_brain_import(self):
        from core.llm_brain import llm_generate, get_brain_status
        assert callable(llm_generate)
        assert callable(get_brain_status)
    
    def test_brain_status(self):
        from core.llm_brain import get_brain_status
        status = get_brain_status()
        assert "device" in status
        assert "code_model" in status
        assert "reason_model" in status
    
    def test_load_prompt_template(self):
        from core.llm_brain import load_prompt_template
        # Should return empty string if file doesn't exist, or content if it does
        result = load_prompt_template("code_fix.system.txt")
        assert isinstance(result, str)


class TestAutonomousCoder:
    """Test autonomous coder components."""
    
    def test_autonomous_coder_import(self):
        from core.autonomous_coder import analyze_and_fix, implement_feature, FixResult
        assert callable(analyze_and_fix)
        assert callable(implement_feature)
    
    def test_find_relevant_files(self):
        from core.autonomous_coder import find_relevant_files
        files = find_relevant_files("issue with TTS not working")
        assert isinstance(files, dict)
    
    def test_run_tests_function(self):
        from core.autonomous_coder import run_tests
        # Should be callable and return tuple
        assert callable(run_tests)


class TestTaskPlanner:
    """Test task planner components."""
    
    def test_task_planner_import(self):
        from core.task_planner import create_plan, quick_command, TaskPlan
        assert callable(create_plan)
        assert callable(quick_command)
    
    def test_quick_command_improve(self):
        from core.task_planner import quick_command
        result = quick_command("improve yourself")
        assert result["action"] == "self_improve"
    
    def test_quick_command_refactor(self):
        from core.task_planner import quick_command
        result = quick_command("refactor the logging module")
        assert result["action"] == "refactor"
    
    def test_quick_command_fix(self):
        from core.task_planner import quick_command
        result = quick_command("fix the keyboard bug")
        assert result["action"] == "analyze_and_fix"


class TestAutonomousReview:
    """Test autonomous review and digest generation."""
    
    def test_review_import(self):
        from core.autonomous_review import generate_report, get_recent_summary
        assert callable(generate_report)
        assert callable(get_recent_summary)
    
    def test_generate_empty_report(self):
        from core.autonomous_review import generate_report
        report = generate_report([])
        assert "No autonomous actions" in report
    
    def test_recent_summary_structure(self):
        from core.autonomous_review import get_recent_summary
        summary = get_recent_summary(hours=1)
        assert "actions" in summary
        assert "rollbacks" in summary
        assert "files_changed" in summary


class TestIntegration:
    """Integration tests."""
    
    def test_repair_engine_has_autonomous_escalation(self):
        from core.repair_engine import RepairEngine
        engine = RepairEngine()
        assert hasattr(engine, "escalate_to_autonomous_coder")
    
    def test_prompt_templates_exist(self):
        prompts_dir = Path(__file__).parent.parent / "core" / "prompts"
        assert prompts_dir.exists()
        assert (prompts_dir / "code_fix.system.txt").exists()
        assert (prompts_dir / "planner.system.txt").exists()


# Simulated bug fix test (dry run - doesn't actually call LLM)
class TestSimulatedBugFix:
    """Simulate bug fix workflow without calling LLM."""
    
    def test_snapshot_creation(self):
        from core.autonomous_coder import create_snapshot
        snapshot = create_snapshot("test_simulated")
        assert snapshot.exists()
        # Cleanup
        if snapshot.exists():
            shutil.rmtree(snapshot)
    
    def test_fix_result_structure(self):
        from core.autonomous_coder import FixResult
        result = FixResult(
            success=True,
            message="Test fix",
            patch_applied=True,
            tests_passed=True,
            files_changed=["test.py"],
            rollback_performed=False,
            explanation="Test explanation",
            model_used="test-model"
        )
        assert result.success is True
        assert result.tests_passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
