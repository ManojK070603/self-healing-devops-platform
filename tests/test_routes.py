from app import create_app

def test_home_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "running"


def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"

def test_unknown_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404

def test_dashboard_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/dashboard")

    assert response.status_code == 200

    data = response.get_json()

    assert data["platform"] == "Self-Healing DevOps Platform"
    assert data["status"] == "operational"
    assert data["demo_data"] is True

    assert data["services"]["total"] == 1
    assert data["services"]["healthy"] == 1
    assert data["services"]["unhealthy"] == 0

    assert data["incidents"]["total"] == 0
    assert data["incidents"]["active"] == 0
    assert data["incidents"]["resolved"] == 0

    assert data["self_healing"]["enabled"] is False
    assert data["self_healing"]["recoveries_today"] == 0