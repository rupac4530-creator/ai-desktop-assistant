# tools/test_stt_long.py
"""
Smoke test for STT (Speech-to-Text) system.
Tests ASR initialization and basic functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_asr_import():
    """Test ASR module can be imported."""
    from speech.asr import ASREngine, get_engine
    assert ASREngine is not None
    print(" ASR import OK")


def test_asr_initialization():
    """Test ASR engine initializes."""
    from speech.asr import get_engine
    
    engine = get_engine()
    assert engine is not None
    print(" ASR engine initialized")


def test_asr_has_model():
    """Test ASR has a model loaded."""
    from speech.asr import get_engine
    
    engine = get_engine()
    assert hasattr(engine, '_model') or hasattr(engine, 'model')
    print(" ASR model present")


def test_asr_device():
    """Test ASR device configuration."""
    import os
    device = os.getenv("DEVICE", "cpu")
    assert device in ["cpu", "cuda", "auto"]
    print(f" ASR device configured: {device}")


if __name__ == "__main__":
    print("=" * 50)
    print("STT LONG SMOKE TESTS")
    print("=" * 50)
    
    tests = [
        test_asr_import,
        test_asr_initialization,
        test_asr_has_model,
        test_asr_device,
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
