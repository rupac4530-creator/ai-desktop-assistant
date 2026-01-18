# tools/test_watchdog.py
"""
Tests for the Watchdog health monitoring system.
"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_watchdog_initialization():
    """Test watchdog initializes correctly."""
    from core.watchdog import get_watchdog, Watchdog
    
    wd = get_watchdog()
    assert isinstance(wd, Watchdog)
    print(" Watchdog initialization OK")

def test_diagnostics_without_components():
    """Test diagnostics runs even without components registered."""
    from core.watchdog import get_watchdog
    
    wd = get_watchdog()
    report = wd.run_diagnostics()
    
    assert report is not None
    assert report.timestamp > 0
    assert report.overall_status is not None
    print(f" Diagnostics OK: status={report.overall_status.value}")

def test_health_status_enum():
    """Test health status enum values."""
    from core.watchdog import HealthStatus
    
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.FAILED.value == "failed"
    print(" HealthStatus enum OK")

def test_component_health_dataclass():
    """Test component health dataclass."""
    from core.watchdog import ComponentHealth, HealthStatus
    import time
    
    ch = ComponentHealth(
        name="test",
        status=HealthStatus.HEALTHY,
        last_check=time.time(),
        message="Test OK"
    )
    
    assert ch.name == "test"
    assert ch.status == HealthStatus.HEALTHY
    print(" ComponentHealth dataclass OK")

def test_diagnostic_report_dataclass():
    """Test diagnostic report dataclass."""
    from core.watchdog import DiagnosticReport, HealthStatus
    import time
    
    report = DiagnosticReport(
        timestamp=time.time(),
        components={},
        overall_status=HealthStatus.HEALTHY,
        issues=[],
        recommendations=[]
    )
    
    assert report.overall_status == HealthStatus.HEALTHY
    assert len(report.issues) == 0
    print(" DiagnosticReport dataclass OK")

def test_status_text():
    """Test human-readable status generation."""
    from core.watchdog import get_watchdog
    
    wd = get_watchdog()
    text = wd.get_status_text()
    
    assert isinstance(text, str)
    assert len(text) > 0
    print(f" Status text: '{text[:50]}...'")

def test_get_status():
    """Test status dict generation."""
    from core.watchdog import get_watchdog
    
    wd = get_watchdog()
    status = wd.get_status()
    
    assert "overall" in status
    assert "issues" in status
    assert "recommendations" in status
    print(f" Status dict: overall={status['overall']}")


if __name__ == "__main__":
    print("=" * 50)
    print("WATCHDOG TESTS")
    print("=" * 50)
    
    tests = [
        test_watchdog_initialization,
        test_diagnostics_without_components,
        test_health_status_enum,
        test_component_health_dataclass,
        test_diagnostic_report_dataclass,
        test_status_text,
        test_get_status,
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
