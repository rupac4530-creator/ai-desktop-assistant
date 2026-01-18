# tools/test_self_update_flow.py
"""
Test self-update flow for Full Autonomy validation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_updater_initialization():
    """Test updater initializes correctly."""
    from core.self_update import get_updater, SelfUpdater
    
    updater = get_updater()
    assert isinstance(updater, SelfUpdater)
    print(" SelfUpdater initialization OK")


def test_status_structure():
    """Test status has required fields."""
    from core.self_update import get_updater
    
    updater = get_updater()
    status = updater.get_status()
    
    required = ["AUTOPILOT", "FULL_AUTONOMY", "enabled", "auto_apply", 
                "check_interval", "whitelist", "maintenance_window", 
                "auto_rollback", "keep_snapshots", "LAST_RUN", "LAST_RESULT"]
    
    for key in required:
        assert key in status, f"Missing key: {key}"
    
    print(" Status structure OK")


def test_maintenance_window():
    """Test maintenance window check."""
    from core.self_update import is_in_maintenance_window
    
    # With 00:00-23:59, should always be in window
    result = is_in_maintenance_window()
    assert result == True
    print(" Maintenance window check OK")


def test_snapshot_dir_exists():
    """Test snapshots directory can be created."""
    from core.watchdog import SNAPSHOTS_DIR
    
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    assert SNAPSHOTS_DIR.exists()
    print(f" Snapshots dir OK: {SNAPSHOTS_DIR}")


def test_log_functions():
    """Test logging functions work."""
    from core.self_update import log_update, log_json, log_run
    
    log_update("Test log message")
    log_json("test_event", {"test": True})
    log_run("Test run log")
    print(" Logging functions OK")


if __name__ == "__main__":
    print("=" * 50)
    print("SELF-UPDATE FLOW TESTS")
    print("=" * 50)
    
    tests = [
        test_updater_initialization,
        test_status_structure,
        test_maintenance_window,
        test_snapshot_dir_exists,
        test_log_functions,
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
