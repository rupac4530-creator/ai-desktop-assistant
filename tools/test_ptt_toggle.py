# tools/test_ptt_toggle.py
"""
Smoke test for PTT (Push-to-Talk) toggle functionality.
Tests keyboard and PTT state management.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_keyboard_import():
    """Test keyboard module can be imported."""
    from ui.keyboard import KeyboardListener
    assert KeyboardListener is not None
    print(" Keyboard import OK")


def test_ptt_config():
    """Test PTT configuration."""
    import os
    ptt_mode = os.getenv("PTT_MODE", "toggle")
    assert ptt_mode in ["toggle", "hold", "toggle+enter"]
    print(f" PTT mode configured: {ptt_mode}")


def test_ptt_hotkey_config():
    """Test PTT hotkey configuration."""
    import os
    hotkey = os.getenv("PTT_HOTKEY", "ctrl+alt+space")
    assert hotkey is not None
    assert len(hotkey) > 0
    print(f" PTT hotkey configured: {hotkey}")


def test_ptt_stop_key():
    """Test PTT stop key configuration."""
    import os
    stop_key = os.getenv("PTT_STOP_KEY", "Enter")
    assert stop_key is not None
    print(f" PTT stop key configured: {stop_key}")


def test_ptt_max_seconds():
    """Test PTT max recording duration."""
    import os
    max_secs = int(os.getenv("PTT_MAX_SECONDS", "300"))
    assert max_secs > 0
    assert max_secs <= 600  # reasonable limit
    print(f" PTT max seconds: {max_secs}")


if __name__ == "__main__":
    print("=" * 50)
    print("PTT TOGGLE SMOKE TESTS")
    print("=" * 50)
    
    tests = [
        test_keyboard_import,
        test_ptt_config,
        test_ptt_hotkey_config,
        test_ptt_stop_key,
        test_ptt_max_seconds,
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
