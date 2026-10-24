
from app.monitoring.incident_manager import IncidentManager


def test_create_incident():
    manager = IncidentManager()

    incident = manager.create_incident(
        service="demo-service",
        reason="Health checks failed",
    )

    assert incident["id"] == 1
    assert incident["service"] == "demo-service"
    assert incident["reason"] == "Health checks failed"
    assert incident["status"] == "open"
    assert incident["created_at"]


def test_incident_ids_increment():
    manager = IncidentManager()

    first = manager.create_incident("service-a", "First failure")
    second = manager.create_incident("service-b", "Second failure")

    assert first["id"] == 1
    assert second["id"] == 2


def test_list_incidents_returns_created_incidents():
    manager = IncidentManager()

    manager.create_incident("service-a", "Failure A")
    manager.create_incident("service-b", "Failure B")

    incidents = manager.list_incidents()

    assert len(incidents) == 2
    assert incidents[0]["service"] == "service-a"
    assert incidents[1]["service"] == "service-b"


def test_list_incidents_does_not_expose_internal_list():
    manager = IncidentManager()
    manager.create_incident("service-a", "Failure A")

    incidents = manager.list_incidents()
    incidents.clear()

    assert len(manager.list_incidents()) == 1


def test_resolve_incident():
    manager = IncidentManager()
    incident = manager.create_incident(
        "demo-service",
        "Health checks failed",
    )

    resolved = manager.resolve_incident(incident["id"])

    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"]


def test_resolving_unknown_incident_returns_none():
    manager = IncidentManager()

    assert manager.resolve_incident(999) is None