# tools/test_rollback.py
"""
Test rollback functionality for Full Autonomy.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_backup_creation():
    """Test backup can be created."""
    from core.self_update import get_updater
    
    updater = get_updater()
    backup_path = updater.create_backup()
    
    assert backup_path is not None
    assert Path(backup_path).exists()
    print(f" Backup created: {Path(backup_path).name}")


def test_snapshot_prune():
    """Test snapshot pruning works."""
    from core.self_update import prune_old_snapshots
    
    # Should not raise
    prune_old_snapshots()
    print(" Snapshot pruning OK")


def test_rollback_config():
    """Test rollback is enabled in config."""
    from core.self_update import SELF_UPDATE_AUTO_ROLLBACK
    
    assert SELF_UPDATE_AUTO_ROLLBACK == True
    print(" Auto-rollback enabled")


def test_keep_snapshots_config():
    """Test snapshot retention config."""
    from core.self_update import SELF_UPDATE_KEEP_SNAPSHOTS
    
    assert SELF_UPDATE_KEEP_SNAPSHOTS >= 7
    print(f" Keeping {SELF_UPDATE_KEEP_SNAPSHOTS} snapshots")


if __name__ == "__main__":
    print("=" * 50)
    print("ROLLBACK TESTS")
    print("=" * 50)
    
    tests = [
        test_backup_creation,
        test_snapshot_prune,
        test_rollback_config,
        test_keep_snapshots_config,
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
