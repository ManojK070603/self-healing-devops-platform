import threading
import time
from unittest.mock import Mock

import pytest

from app.monitoring.monitor_runner import MonitorRunner


def test_run_once_checks_each_service():
    first = Mock()
    first.name = "service-one"
    first.check_once.return_value = {
        "service": "service-one",
        "health": {"healthy": True},
    }

    second = Mock()
    second.name = "service-two"
    second.check_once.return_value = {
        "service": "service-two",
        "health": {"healthy": True},
    }

    runner = MonitorRunner(
        [first, second],
        interval_seconds=30,
    )

    results = runner.run_once()

    first.check_once.assert_called_once()
    second.check_once.assert_called_once()
    assert len(results) == 2


def test_runner_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        MonitorRunner([], interval_seconds=30)

    with pytest.raises(ValueError):
        MonitorRunner([Mock()], interval_seconds=0)


def test_runner_continues_if_one_service_raises():
    broken = Mock()
    broken.name = "broken-service"
    broken.check_once.side_effect = RuntimeError("simulated error")

    healthy = Mock()
    healthy.name = "healthy-service"
    healthy.check_once.return_value = {
        "service": "healthy-service",
        "health": {"healthy": True},
    }

    runner = MonitorRunner(
        [broken, healthy],
        interval_seconds=30,
    )

    results = runner.run_once()

    assert "error" in results[0]
    assert results[1]["service"] == "healthy-service"
    healthy.check_once.assert_called_once()


def test_runner_starts_and_stops():
    service = Mock()
    service.name = "demo-service"
    service.check_once.return_value = {
        "service": "demo-service",
        "health": {"healthy": True},
    }

    runner = MonitorRunner(
        [service],
        interval_seconds=30,
    )

    assert runner.start() is True

    try:
        deadline = time.monotonic() + 2

        while service.check_once.call_count == 0:
            if time.monotonic() >= deadline:
                pytest.fail("Monitoring runner did not perform a check")
            threading.Event().wait(0.01)

        assert runner.is_running
        assert runner.stop(timeout=2) is True
        assert runner.is_running is False
    finally:
        runner.stop(timeout=2)


def test_start_does_not_create_duplicate_running_threads():
    service = Mock()
    service.name = "demo-service"
    service.check_once.return_value = {
        "service": "demo-service",
        "health": {"healthy": True},
    }

    runner = MonitorRunner([service], interval_seconds=30)

    assert runner.start() is True

    try:
        assert runner.start() is False
    finally:
        assert runner.stop(timeout=2) is True
