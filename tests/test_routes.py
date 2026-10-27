
from app import create_app
from unittest.mock import patch


def test_home_endpoint():
    client = create_app().test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json()["status"] == "running"


def test_health_endpoint():
    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_unknown_endpoint():
    client = create_app().test_client()
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404


def test_dashboard_endpoint():
    client = create_app().test_client()
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.get_json()

    assert data["platform"] == "Self-Healing DevOps Platform"
    assert data["status"] == "operational"
    assert data["demo_data"] is True

    assert data["services"]["total"] == 1
    assert data["services"]["healthy"] == 1
    assert data["services"]["unhealthy"] == 0

    assert data["incidents"]["total"] == 3
    assert data["incidents"]["active"] == 2
    assert data["incidents"]["resolved"] == 1

    assert data["deployments"]["total"] == 2
    assert data["deployments"]["successful"] == 1
    assert data["deployments"]["in_progress"] == 1

    assert data["security"]["total_scans"] == 2
    assert data["security"]["findings"] == {
        "critical": 0,
        "high": 2,
        "medium": 5,
        "low": 5,
    }

    assert data["self_healing"]["enabled"] is False
    assert data["self_healing"]["recoveries_today"] == 0


def test_deployments_endpoint():
    client = create_app().test_client()
    response = client.get("/api/deployments")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is True
    assert data["total"] == 2
    assert len(data["deployments"]) == 2
    assert data["deployments"][0]["status"] == "success"
    assert data["deployments"][1]["status"] == "in_progress"


def test_incidents_endpoint():
    client = create_app().test_client()
    response = client.get("/api/incidents")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is True
    assert data["total"] == 3
    assert len(data["incidents"]) == 3

    incident = data["incidents"][0]
    assert "id" in incident
    assert "title" in incident
    assert incident["severity"] in ["low", "medium", "high", "critical"]
    assert incident["status"] in ["open", "investigating", "resolved"]
    assert "service" in incident
    assert "created_at" in incident


def test_metrics_endpoint():
    client = create_app().test_client()
    response = client.get("/api/metrics")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is True
    metrics = data["metrics"]

    assert 0 <= metrics["cpu_usage_percent"] <= 100
    assert 0 <= metrics["memory_usage_percent"] <= 100
    assert metrics["request_count"] >= 0
    assert 0 <= metrics["error_rate_percent"] <= 100
    assert metrics["response_time_ms"] >= 0


def test_security_scans_endpoint():
    client = create_app().test_client()
    response = client.get("/api/security-scans")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is True
    assert data["total"] == 2
    assert len(data["scans"]) == 2

    scan = data["scans"][0]
    assert "scanner" in scan
    assert scan["status"] in ["completed", "failed", "in_progress"]
    assert "scanned_at" in scan

    findings = scan["findings"]
    for severity in ["critical", "high", "medium", "low"]:
        assert severity in findings
        assert isinstance(findings[severity], int)
        assert findings[severity] >= 0

def test_monitoring_metrics_endpoint():
    client = create_app().test_client()

    response = client.get("/api/monitoring/metrics")

    assert response.status_code == 200

    data = response.get_json()

    assert data["demo_data"] is False
    assert data["metrics"]["total_checks"] == 0
    assert data["metrics"]["healthy_checks"] == 0
    assert data["metrics"]["unhealthy_checks"] == 0
    assert data["metrics"]["success_rate_percent"] is None


def test_monitoring_metrics_endpoint_returns_recorded_data():
    app = create_app()
    client = app.test_client()

    history_store = app.extensions["monitoring_history_store"]

    history_store.record({
        "service": "demo-api",
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 25.0,
        "error": None,
    })

    history_store.record({
        "service": "demo-api",
        "healthy": False,
        "status_code": 503,
        "response_time_ms": 40.0,
        "error": "Service unavailable",
    })

    response = client.get(
        "/api/monitoring/metrics?service=demo-api"
    )

    assert response.status_code == 200

    data = response.get_json()
    metrics = data["metrics"]

    assert data["demo_data"] is False
    assert data["service"] == "demo-api"
    assert metrics["total_checks"] == 2
    assert metrics["healthy_checks"] == 1
    assert metrics["unhealthy_checks"] == 1
    assert metrics["success_rate_percent"] == 50.0
    assert metrics["average_response_time_ms"] == 32.5


def test_app_registers_monitor_runner_with_shared_history_store():
    app = create_app()

    runner = app.extensions["monitor_runner"]
    history_store = app.extensions["monitoring_history_store"]

    assert runner.is_running is False
    assert len(runner.monitored_services) == 1
    assert runner.monitored_services[0].name == "platform-api"
    assert (
        runner.monitored_services[0].history_store
        is history_store
    )


from unittest.mock import patch


def test_runner_health_check_appears_in_metrics_api():
    app = create_app()
    client = app.test_client()
    runner = app.extensions["monitor_runner"]

    healthy_result = {
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 18.0,
        "error": None,
    }

    with patch(
        "app.monitoring.monitor_service.check_http_health",
        return_value=healthy_result,
    ):
        results = runner.run_once()

    assert results[0]["service"] == "platform-api"
    assert results[0]["health"]["healthy"] is True
    assert results[0]["health"]["consecutive_failures"] == 0

    response = client.get(
        "/api/monitoring/metrics?service=platform-api"
    )

    assert response.status_code == 200
    data = response.get_json()
    metrics = data["metrics"]

    assert data["demo_data"] is False
    assert metrics["total_checks"] == 1
    assert metrics["healthy_checks"] == 1
    assert metrics["unhealthy_checks"] == 0
    assert metrics["success_rate_percent"] == 100.0
    assert metrics["average_response_time_ms"] == 18.0

def test_live_dashboard_returns_empty_state_without_checks():
    client = create_app().test_client()

    response = client.get("/api/dashboard/live")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is False
    assert data["services"]["total"] == 0
    assert data["services"]["healthy"] == 0
    assert data["services"]["unhealthy"] == 0
    assert data["services"]["items"] == []


def test_live_dashboard_reflects_recorded_health_checks():
    app = create_app()
    client = app.test_client()
    history_store = app.extensions["monitoring_history_store"]

    history_store.record({
        "service": "demo-api",
        "healthy": True,
        "status_code": 200,
        "response_time_ms": 18.0,
        "error": None,
    })

    history_store.record({
        "service": "worker-api",
        "healthy": False,
        "status_code": 503,
        "response_time_ms": 35.0,
        "error": "Service unavailable",
    })

    response = client.get("/api/dashboard/live")

    assert response.status_code == 200
    data = response.get_json()

    assert data["demo_data"] is False
    assert data["services"]["total"] == 2
    assert data["services"]["healthy"] == 1
    assert data["services"]["unhealthy"] == 1

    statuses = {
        service["name"]: service["status"]
        for service in data["services"]["items"]
    }

    assert statuses["demo-api"] == "healthy"
    assert statuses["worker-api"] == "unhealthy"


def test_monitoring_check_endpoint_returns_real_monitoring_result(monkeypatch):
    app = create_app()
    client = app.test_client()
    runner = app.extensions["monitor_runner"]

    expected_results = [
        {
            "service": "platform-api",
            "health": {
                "healthy": True,
                "consecutive_failures": 0,
                "threshold": 3,
                "unhealthy": False,
                "last_result": {
                    "healthy": True,
                    "status_code": 200,
                    "response_time_ms": 12.0,
                    "error": None,
                },
            },
            "incident_created": False,
            "active_incident": None,
            "recovery": None,
            "recovery_verification": None,
        }
    ]

    def fake_run_once():
        return expected_results

    monkeypatch.setattr(runner, "run_once", fake_run_once)

    response = client.post("/api/monitoring/check")

    assert response.status_code == 200

    data = response.get_json()

    assert data["demo_data"] is False
    assert data["results"] == expected_results


def test_monitoring_check_endpoint_records_health_metrics(monkeypatch):
    app = create_app()
    client = app.test_client()
    runner = app.extensions["monitor_runner"]
    history_store = app.extensions["monitoring_history_store"]

    def fake_run_once():
        history_store.record({
            "service": "platform-api",
            "healthy": True,
            "status_code": 200,
            "response_time_ms": 18.0,
            "error": None,
        })

        return [{"service": "platform-api"}]

    monkeypatch.setattr(runner, "run_once", fake_run_once)

    response = client.post("/api/monitoring/check")

    assert response.status_code == 200

    metrics_response = client.get(
        "/api/monitoring/metrics?service=platform-api"
    )

    assert metrics_response.status_code == 200

    metrics = metrics_response.get_json()["metrics"]

    assert metrics["total_checks"] == 1
    assert metrics["healthy_checks"] == 1
    assert metrics["unhealthy_checks"] == 0
    assert metrics["success_rate_percent"] == 100.0
    assert metrics["average_response_time_ms"] == 18.0
