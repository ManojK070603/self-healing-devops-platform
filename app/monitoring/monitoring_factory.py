
"""Build monitoring components with shared application state."""

from app.monitoring.incident_manager import IncidentManager
from app.monitoring.monitor_runner import MonitorRunner
from app.monitoring.monitor_service import MonitoredService


def create_monitor_runner(
    history_store,
    service_configs,
    interval_seconds=30,
    incident_manager=None,
    recovery_coordinator=None,
):
    """Build a runner without starting background monitoring."""
    if not service_configs:
        raise ValueError("At least one service configuration is required")

    manager = incident_manager or IncidentManager()
    monitored_services = []

    for config in service_configs:
        monitored_services.append(
            MonitoredService(
                name=config["name"],
                url=config["url"],
                incident_manager=manager,
                history_store=history_store,
                recovery_coordinator=recovery_coordinator,
            )
        )

    return MonitorRunner(
        monitored_services,
        interval_seconds=interval_seconds,
    )
