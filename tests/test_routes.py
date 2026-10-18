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