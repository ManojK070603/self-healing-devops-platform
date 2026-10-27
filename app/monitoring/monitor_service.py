
import time

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
        history_store=None,
        recovery_verification_attempts=5,
        recovery_verification_interval=1.0,
    ):
        if recovery_verification_attempts < 1:
            raise ValueError(
                "recovery_verification_attempts must be at least 1"
            )

        if recovery_verification_interval < 0:
            raise ValueError(
                "recovery_verification_interval cannot be negative"
            )

        self.name = name
        self.url = url
        self.timeout = timeout
        self.monitor = HealthMonitor(
            failure_threshold=failure_threshold
        )
        self.incident_manager = incident_manager
        self.recovery_coordinator = recovery_coordinator
        self.active_incident = None
        self.history_store = history_store
        self.recovery_verification_attempts = (
            recovery_verification_attempts
        )
        self.recovery_verification_interval = (
            recovery_verification_interval
        )

    def _record_history(self, result):
        """Save a health result when history storage is configured."""
        if self.history_store is not None:
            self.history_store.record({
                "service": self.name,
                **result,
            })

    def _verify_recovery(self):
        """Retry health checks until healthy or attempts are exhausted."""
        last_result = None

        for attempt in range(self.recovery_verification_attempts):
            if attempt > 0:
                time.sleep(self.recovery_verification_interval)

            last_result = check_http_health(
                self.url,
                timeout=self.timeout,
            )
            self._record_history(last_result)

            if last_result["healthy"]:
                return last_result

        return last_result

    def check_once(self):
        """Run one monitoring check and handle incidents and recovery."""
        health_result = check_http_health(
            self.url,
            timeout=self.timeout,
        )
        self._record_history(health_result)

        monitor_result = self.monitor.record_result(health_result)

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
                    recovery_verification = self._verify_recovery()
                    health_result = recovery_verification

                    # Verification retries are not separate regular
                    # monitoring checks. Record only the final healthy
                    # result to reset the consecutive-failure counter.
                    if recovery_verification["healthy"]:
                        monitor_result = self.monitor.record_result(
                            recovery_verification
                        )

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
