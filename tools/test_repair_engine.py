# tools/test_repair_engine.py
"""
Tests for the RepairEngine repair actions system.
"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_repair_engine_initialization():
    """Test repair engine initializes correctly."""
    from core.repair_engine import get_repair_engine, RepairEngine
    
    engine = get_repair_engine()
    assert isinstance(engine, RepairEngine)
    print(" RepairEngine initialization OK")

def test_repair_engine_singleton():
    """Test repair engine singleton pattern."""
    from core.repair_engine import get_repair_engine
    
    engine1 = get_repair_engine()
    engine2 = get_repair_engine()
    
    assert engine1 is engine2
    print(" RepairEngine singleton OK")

def test_repair_result_enum():
    """Test repair result enum values."""
    from core.repair_engine import RepairResult
    
    assert RepairResult.SUCCESS.value == "success"
    assert RepairResult.FAILED.value == "failed"
    assert RepairResult.PARTIAL.value == "partial"
    assert RepairResult.SKIPPED.value == "skipped"
    print(" RepairResult enum OK")

def test_repair_action_dataclass():
    """Test repair action dataclass."""
    from core.repair_engine import RepairAction, RepairResult
    
    action = RepairAction(
        name="test_action",
        result=RepairResult.SUCCESS,
        message="Test successful",
        duration=1.5,
        snapshot_path="/path/to/snapshot"
    )
    
    assert action.name == "test_action"
    assert action.result == RepairResult.SUCCESS
    assert action.duration == 1.5
    print(" RepairAction dataclass OK")

def test_snapshot_creation():
    """Test snapshot directory creation."""
    from core.repair_engine import create_snapshot
    
    snapshot_path = create_snapshot("test")
    assert os.path.exists(snapshot_path)
    print(f" Snapshot creation OK: {snapshot_path}")

def test_set_components():
    """Test setting component references."""
    from core.repair_engine import get_repair_engine
    
    engine = get_repair_engine()
    engine.set_components(asr=None, tts=None, keyboard=None, avatar=None)
    print(" set_components OK")

def test_reset_ptt_state_action():
    """Test PTT state reset action."""
    from core.repair_engine import get_repair_engine, RepairResult
    
    engine = get_repair_engine()
    result = engine.reset_ptt_state()
    
    assert result.name == "reset_ptt_state"
    assert result.result in [RepairResult.SUCCESS, RepairResult.FAILED, RepairResult.SKIPPED]
    print(f" reset_ptt_state OK: {result.result.value}")

def test_rebind_hotkeys_action():
    """Test hotkey rebind action."""
    from core.repair_engine import get_repair_engine, RepairResult
    
    engine = get_repair_engine()
    result = engine.rebind_hotkeys()
    
    assert result.name == "rebind_hotkeys"
    assert result.result in [RepairResult.SUCCESS, RepairResult.FAILED, RepairResult.SKIPPED]
    print(f" rebind_hotkeys OK: {result.result.value}")


if __name__ == "__main__":
    print("=" * 50)
    print("REPAIR ENGINE TESTS")
    print("=" * 50)
    
    tests = [
        test_repair_engine_initialization,
        test_repair_engine_singleton,
        test_repair_result_enum,
        test_repair_action_dataclass,
        test_snapshot_creation,
        test_set_components,
        test_reset_ptt_state_action,
        test_rebind_hotkeys_action,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f" {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    exit(0 if failed == 0 else 1)
