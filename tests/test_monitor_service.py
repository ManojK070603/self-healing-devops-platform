
from unittest.mock import patch

from app.monitoring.incident_manager import IncidentManager
from app.monitoring.monitor_service import MonitoredService


def test_three_failures_create_one_incident():
    manager = IncidentManager()

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=3,
    )

    failed_result = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        return_value=failed_result,
    ):
        first = service.check_once()
        second = service.check_once()
        third = service.check_once()
        fourth = service.check_once()

    assert first["incident_created"] is False
    assert second["incident_created"] is False
    assert third["incident_created"] is True
    assert fourth["incident_created"] is False

    assert len(manager.list_incidents()) == 1
    assert manager.list_incidents()[0]["service"] == "demo-service"


def test_successful_check_resets_failure_count():
    manager = IncidentManager()

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=3,
    )

    failed_result = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    healthy_result = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 100,
        "error": None,
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        side_effect=[
            failed_result,
            failed_result,
            healthy_result,
        ],
    ):
        service.check_once()
        service.check_once()
        result = service.check_once()

    assert result["health"]["consecutive_failures"] == 0
    assert result["health"]["unhealthy"] is False
    assert result["incident_created"] is False
    assert manager.list_incidents() == []

def test_recovery_resolves_existing_incident():
    manager = IncidentManager()

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=2,
    )

    failed_result = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    healthy_result = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 100,
        "error": None,
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        side_effect=[
            failed_result,
            failed_result,
            healthy_result,
        ],
    ):
        service.check_once()
        failure_result = service.check_once()
        recovery_result = service.check_once()

    assert failure_result["incident_created"] is True
    assert recovery_result["health"]["healthy"] is True
    assert recovery_result["active_incident"] is None

    incidents = manager.list_incidents()
    assert len(incidents) == 1
    assert incidents[0]["status"] == "resolved"
    assert incidents[0]["resolved_at"]

def test_recovery_is_requested_once_when_incident_is_created():
    from unittest.mock import Mock

    manager = IncidentManager()
    coordinator = Mock()
    coordinator.attempt_recovery.return_value = {
        "service": "demo-service",
        "attempted": False,
        "success": False,
        "message": "Recovery blocked by policy",
    }

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=2,
        recovery_coordinator=coordinator,
    )

    failed_result = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 3000,
        "error": "Simulated connection failure",
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        return_value=failed_result,
    ):
        first = service.check_once()
        second = service.check_once()
        third = service.check_once()

    assert first["incident_created"] is False
    assert first["recovery"] is None

    assert second["incident_created"] is True
    assert second["recovery"]["message"] == (
        "Recovery blocked by policy"
    )

    assert third["incident_created"] is False
    assert third["recovery"] is None

    coordinator.attempt_recovery.assert_called_once_with(
        "demo-service"
    )
    assert len(manager.list_incidents()) == 1
def test_successful_recovery_is_verified_and_resolves_incident():
    from unittest.mock import Mock

    manager = IncidentManager()
    coordinator = Mock()
    coordinator.attempt_recovery.return_value = {
        "service": "demo-service",
        "attempted": True,
        "success": True,
        "message": "Recovery action completed",
    }

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=2,
        recovery_coordinator=coordinator,
    )

    failed = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 100,
        "error": "Simulated failure",
    }
    healthy = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 50,
        "error": None,
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        side_effect=[failed, failed, healthy],
    ) as health_check:
        service.check_once()
        result = service.check_once()

    assert health_check.call_count == 3
    assert result["recovery"]["success"] is True
    assert result["recovery_verification"]["healthy"] is True
    assert result["health"]["healthy"] is True
    assert result["active_incident"] is None

    incident = manager.list_incidents()[0]
    assert incident["status"] == "resolved"
    assert incident["resolved_at"]


def test_recovery_action_success_does_not_resolve_unhealthy_service():
    from unittest.mock import Mock

    manager = IncidentManager()
    coordinator = Mock()
    coordinator.attempt_recovery.return_value = {
        "service": "demo-service",
        "attempted": True,
        "success": True,
        "message": "Recovery action completed",
    }

    service = MonitoredService(
        name="demo-service",
        url="http://example.invalid/health",
        incident_manager=manager,
        failure_threshold=2,
        recovery_coordinator=coordinator,
    )

    failed = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": 100,
        "error": "Simulated failure",
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        return_value=failed,
    ) as health_check:
        service.check_once()
        result = service.check_once()

    assert health_check.call_count == 3
    assert result["recovery"]["success"] is True
    assert result["recovery_verification"]["healthy"] is False
    assert result["active_incident"] is not None

    incident = manager.list_incidents()[0]
    assert incident["status"] == "open"
    assert "resolved_at" not in incident