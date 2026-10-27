
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
