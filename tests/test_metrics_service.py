from app.monitoring.history_store import MonitoringHistoryStore
from app.monitoring.metrics_service import MonitoringMetricsService


def test_metrics_are_calculated_from_history():
    store = MonitoringHistoryStore()
    store.record({
        "service": "demo-api",
        "healthy": True,
        "response_time_ms": 20,
    })
    store.record({
        "service": "demo-api",
        "healthy": False,
        "response_time_ms": 60,
    })

    metrics = MonitoringMetricsService(store).get_metrics()

    assert metrics["total_checks"] == 2
    assert metrics["healthy_checks"] == 1
    assert metrics["unhealthy_checks"] == 1
    assert metrics["success_rate_percent"] == 50.0
    assert metrics["average_response_time_ms"] == 40.0
    assert metrics["latest_response_time_ms"] == 60
    assert metrics["latest_status"] == "unhealthy"


def test_metrics_for_unknown_service_are_empty():
    store = MonitoringHistoryStore()

    metrics = MonitoringMetricsService(store).get_metrics(
        "unknown-service"
    )

    assert metrics["total_checks"] == 0
    assert metrics["success_rate_percent"] is None
    assert metrics["average_response_time_ms"] is None
    assert metrics["latest_status"] is None


def test_metrics_can_be_filtered_by_service():
    store = MonitoringHistoryStore()
    store.record({
        "service": "api-one",
        "healthy": True,
        "response_time_ms": 10,
    })
    store.record({
        "service": "api-two",
        "healthy": False,
        "response_time_ms": 100,
    })

    metrics = MonitoringMetricsService(store).get_metrics("api-one")

    assert metrics["total_checks"] == 1
    assert metrics["healthy_checks"] == 1
    assert metrics["success_rate_percent"] == 100.0
