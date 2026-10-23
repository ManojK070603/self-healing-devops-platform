
from app import create_app


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
