from app.monitoring.history_store import MonitoringHistoryStore


def test_record_and_retrieve_history():
    store = MonitoringHistoryStore()

    result = {
        "service": "demo-api",
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 25.5,
    }

    recorded = store.record(result)

    assert recorded["service"] == "demo-api"
    assert recorded["healthy"] is True
    assert recorded["status_code"] == 200
    assert recorded["response_time_ms"] == 25.5
    assert "timestamp" in recorded

    history = store.get_history("demo-api")

    assert len(history) == 1
    assert history[0]["service"] == "demo-api"


def test_history_is_isolated_by_service():
    store = MonitoringHistoryStore()

    store.record({"service": "api-one", "healthy": True})
    store.record({"service": "api-two", "healthy": False})

    assert len(store.get_history("api-one")) == 1
    assert len(store.get_history("api-two")) == 1
    assert store.get_history("unknown") == []


def test_history_respects_max_records():
    store = MonitoringHistoryStore(max_records=2)

    store.record({"service": "demo-api", "healthy": True})
    store.record({"service": "demo-api", "healthy": False})
    store.record({"service": "demo-api", "healthy": True})

    history = store.get_history("demo-api")

    assert len(history) == 2
    assert history[-1]["healthy"] is True


def test_record_does_not_expose_internal_state():
    store = MonitoringHistoryStore()

    result = {"service": "demo-api", "healthy": True}
    recorded = store.record(result)

    recorded["healthy"] = False
    history = store.get_history("demo-api")

    assert history[0]["healthy"] is True
