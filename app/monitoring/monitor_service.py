from app.monitoring.health_checker import (
    HealthMonitor,
    check_http_health,
)


class MonitoredService:
    """Connect health checks, incidents, and controlled recovery."""

    def __init__(
        self,
        name,
        url,
        incident_manager,
        failure_threshold=3,
        timeout=3,
        recovery_coordinator=None,
    ):
        self.name = name
        self.url = url
        self.timeout = timeout
        self.monitor = HealthMonitor(
            failure_threshold=failure_threshold
        )
        self.incident_manager = incident_manager
        self.recovery_coordinator = recovery_coordinator
        self.active_incident = None

    def check_once(self):
        health_result = check_http_health(
            self.url,
            timeout=self.timeout,
        )

        monitor_result = self.monitor.record_result(
            health_result
        )

        incident_created = False
        recovery_result = None
        recovery_verification = None

        if (
            monitor_result["unhealthy"]
            and self.active_incident is None
        ):
            reason = (
                health_result["error"]
                or (
                    "Health check failed with HTTP status "
                    f"{health_result['status_code']}"
                )
            )

            self.active_incident = (
                self.incident_manager.create_incident(
                    service=self.name,
                    reason=(
                        f"{self.monitor.failure_threshold} "
                        "consecutive health checks failed: "
                        f"{reason}"
                    ),
                )
            )

            incident_created = True

            if self.recovery_coordinator is not None:
                recovery_result = (
                    self.recovery_coordinator.attempt_recovery(
                        self.name
                    )
                )

                if (
                    recovery_result.get("attempted")
                    and recovery_result.get("success")
                ):
                    recovery_verification = check_http_health(
                        self.url,
                        timeout=self.timeout,
                    )

                    monitor_result = self.monitor.record_result(
                        recovery_verification
                    )

                    health_result = recovery_verification

        if (
            health_result["healthy"]
            and self.active_incident is not None
        ):
            self.incident_manager.resolve_incident(
                self.active_incident["id"]
            )
            self.active_incident = None

        return {
            "service": self.name,
            "health": monitor_result,
            "incident_created": incident_created,
            "active_incident": self.active_incident,
            "recovery": recovery_result,
            "recovery_verification": recovery_verification,
        }