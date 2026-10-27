
from unittest.mock import patch

from app.monitoring.history_store import MonitoringHistoryStore
from app.monitoring.monitoring_factory import create_monitor_runner


def test_factory_connects_services_to_shared_history_store():
    history_store = MonitoringHistoryStore()

    runner = create_monitor_runner(
        history_store=history_store,
        service_configs=[
            {
                "name": "demo-api",
                "url": "http://example.invalid/health",
            }
        ],
    )

    service = runner.monitored_services[0]

    assert service.name == "demo-api"
    assert service.history_store is history_store
    assert runner.is_running is False


def test_factory_runner_records_a_health_check():
    history_store = MonitoringHistoryStore()

    runner = create_monitor_runner(
        history_store=history_store,
        service_configs=[
            {
                "name": "demo-api",
                "url": "http://example.invalid/health",
            }
        ],
    )

    healthy_result = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 12.0,
        "error": None,
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        return_value=healthy_result,
    ):
        results = runner.run_once()

    assert results[0]["service"] == "demo-api"

    records = history_store.get_history("demo-api")
    assert len(records) == 1
    assert records[0]["healthy"] is True
    assert records[0]["response_time_ms"] == 12.0

def test_factory_connects_recovery_coordinator_to_service():
    from unittest.mock import Mock

    history_store = MonitoringHistoryStore()
    coordinator = Mock()

    runner = create_monitor_runner(
        history_store=history_store,
        service_configs=[
            {
                "name": "demo-api",
                "url": "http://example.invalid/health",
            }
        ],
        recovery_coordinator=coordinator,
    )

    service = runner.monitored_services[0]

    assert service.recovery_coordinator is coordinator
    assert runner.is_running is False


def test_application_recovery_is_disabled_by_default():
    from app import create_app

    app = create_app()
    service = app.extensions["monitor_runner"].monitored_services[0]

    assert app.config["RECOVERY_ENABLED"] is False
    assert service.recovery_coordinator is None
    assert "recovery_coordinator" not in app.extensions


def test_enabled_recovery_requires_container_allowlist():
    import pytest

    from app import create_app

    with pytest.raises(
        ValueError,
        match="explicit container allowlist",
    ):
        create_app({"RECOVERY_ENABLED": True})


def test_enabled_recovery_is_wired_to_monitoring_service():
    from app import create_app
    from app.recovery.docker_recovery_action import DockerRecoveryAction
    from app.recovery.recovery_coordinator import RecoveryCoordinator

    app = create_app({
        "RECOVERY_ENABLED": True,
        "RECOVERY_ALLOWED_CONTAINERS": {
            "platform-api": "test-platform-container",
        },
    })

    service = app.extensions["monitor_runner"].monitored_services[0]
    coordinator = app.extensions["recovery_coordinator"]

    assert isinstance(coordinator, RecoveryCoordinator)
    assert isinstance(
        coordinator.recovery_action,
        DockerRecoveryAction,
    )
    assert coordinator.policy.enabled is True
    assert service.recovery_coordinator is coordinator
    assert service.recovery_coordinator.recovery_action.allowed_containers == {
        "platform-api": "test-platform-container",
    }
    assert app.extensions["monitor_runner"].is_running is False
