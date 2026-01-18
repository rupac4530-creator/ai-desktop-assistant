# tools/test_core_smoke.py
"""
Core smoke tests for Full Autonomy validation.
These tests must pass before any auto-apply.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_main_controller_import():
    """Test main controller can be imported."""
    from core.main_controller import MainController
    assert MainController is not None
    print(" MainController import OK")


def test_self_update_import():
    """Test self-update module can be imported."""
    from core.self_update import SelfUpdater, get_updater
    assert SelfUpdater is not None
    updater = get_updater()
    assert updater is not None
    print(" SelfUpdater import OK")


def test_notify_import():
    """Test notify module can be imported."""
    from core.notify import notify
    assert notify is not None
    print(" Notify import OK")


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


def test_tts_import():
    """Test TTS can be imported."""
    from speech.local_tts import LocalTTS
    assert LocalTTS is not None
    print(" LocalTTS import OK")


def test_asr_import():
    """Test ASR can be imported."""
    from speech.asr import ASREngine
    assert ASREngine is not None
    print(" ASREngine import OK")


def test_env_full_autonomy():
    """Test environment is configured for full autonomy."""
    from dotenv import load_dotenv
    load_dotenv()
    
    auto_apply = os.getenv("SELF_UPDATE_AUTO_APPLY", "false").lower()
    assert auto_apply == "true", "SELF_UPDATE_AUTO_APPLY should be true"
    
    require_approval = os.getenv("SELF_UPDATE_REQUIRE_APPROVAL_FOR_CORE", "true").lower()
    assert require_approval == "false", "SELF_UPDATE_REQUIRE_APPROVAL_FOR_CORE should be false"
    
    print(" Full autonomy config OK")


def test_self_update_status():
    """Test self-update status returns correct structure."""
    from core.self_update import get_updater
    
    updater = get_updater()
    status = updater.get_status()
    
    assert "AUTOPILOT" in status
    assert "FULL_AUTONOMY" in status
    assert "LAST_RUN" in status
    assert "LAST_RESULT" in status
    print(f" Status: AUTOPILOT={status['AUTOPILOT']}, FULL_AUTONOMY={status['FULL_AUTONOMY']}")


if __name__ == "__main__":
    print("=" * 50)
    print("CORE SMOKE TESTS")
    print("=" * 50)
    
    tests = [
        test_main_controller_import,
        test_self_update_import,
        test_notify_import,
        test_watchdog_import,
        test_repair_engine_import,
        test_tts_import,
        test_asr_import,
        test_env_full_autonomy,
        test_self_update_status,
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
