# tools/test_multitask.py
"""
Smoke test for multitask/orchestration functionality.
Tests core system integration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_main_controller_import():
    """Test main controller can be imported."""
    from core.main_controller import MainController
    assert MainController is not None
    print(" MainController import OK")


def test_watchdog_import():
    """Test watchdog can be imported."""
    from core.watchdog import Watchdog, get_watchdog
    assert Watchdog is not None
    print(" Watchdog import OK")


def test_repair_engine_import():
    """Test repair engine can be imported."""
    from core.repair_engine import RepairEngine, get_repair_engine
    assert RepairEngine is not None
    print(" RepairEngine import OK")


def test_self_heal_planner_import():
    """Test self-heal planner can be imported."""
    from core.self_heal_planner import SelfHealPlanner
    assert SelfHealPlanner is not None
    print(" SelfHealPlanner import OK")


def test_approval_manager_import():
    """Test approval manager can be imported."""
    from core.approval import ApprovalManager
    assert ApprovalManager is not None
    print(" ApprovalManager import OK")


def test_self_updater_import():
    """Test self updater can be imported."""
    from core.self_update import SelfUpdater, get_updater
    assert SelfUpdater is not None
    print(" SelfUpdater import OK")


def test_tts_import():
    """Test TTS can be imported."""
    from speech.local_tts import LocalTTS
    assert LocalTTS is not None
    print(" LocalTTS import OK")


def test_env_loaded():
    """Test environment variables loaded."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    assert os.getenv("SELF_HEAL_ENABLED") is not None
    print(" Environment loaded")


if __name__ == "__main__":
    print("=" * 50)
    print("MULTITASK SMOKE TESTS")
    print("=" * 50)
    
    tests = [
        test_main_controller_import,
        test_watchdog_import,
        test_repair_engine_import,
        test_self_heal_planner_import,
        test_approval_manager_import,
        test_self_updater_import,
        test_tts_import,
        test_env_loaded,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f" {test.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    exit(0 if failed == 0 else 1)
