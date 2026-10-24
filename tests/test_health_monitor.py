
import pytest

from app.monitoring.health_checker import HealthMonitor


def test_monitor_starts_healthy_with_zero_failures():
    monitor = HealthMonitor(failure_threshold=3)

    assert monitor.consecutive_failures == 0
    assert monitor.failure_threshold == 3


def test_monitor_marks_unhealthy_at_failure_threshold():
    monitor = HealthMonitor(failure_threshold=3)

    failed = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    monitor.record_result(failed)
    monitor.record_result(failed)
    result = monitor.record_result(failed)

    assert result["consecutive_failures"] == 3
    assert result["unhealthy"] is True


def test_success_resets_consecutive_failures():
    monitor = HealthMonitor(failure_threshold=3)

    failed = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    healthy = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 100,
        "error": None,
    }

    monitor.record_result(failed)
    monitor.record_result(failed)
    result = monitor.record_result(healthy)

    assert result["consecutive_failures"] == 0
    assert result["healthy"] is True
    assert result["unhealthy"] is False


def test_failure_threshold_must_be_positive():
    with pytest.raises(ValueError):
        HealthMonitor(failure_threshold=0)
