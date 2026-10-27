
class MonitoringMetricsService:
    """Calculate service metrics from recorded health-check results."""

    def __init__(self, history_store):
        self.history_store = history_store

    def get_metrics(self, service_name=None):
        """Calculate aggregate metrics, optionally for one service."""
        if service_name is not None:
            records = self.history_store.get_history(service_name)
        else:
            records = []

            # The store will expose service names in the next step.
            for name in self.history_store.get_service_names():
                records.extend(self.history_store.get_history(name))

        total = len(records)
        healthy = sum(record.get("healthy") is True for record in records)
        unhealthy = total - healthy

        response_times = [
            record["response_time_ms"]
            for record in records
            if isinstance(record.get("response_time_ms"), (int, float))
            and record["response_time_ms"] >= 0
        ]

        return {
            "total_checks": total,
            "healthy_checks": healthy,
            "unhealthy_checks": unhealthy,
            "success_rate_percent": (
                round(healthy / total * 100, 2) if total else None
            ),
            "average_response_time_ms": (
                round(sum(response_times) / len(response_times), 2)
                if response_times else None
            ),
            "latest_response_time_ms": (
                response_times[-1] if response_times else None
            ),
           "latest_status": (
                None if not records
                else "healthy" if records[-1].get("healthy") is True
                else "unhealthy"
            ),
            "latest_timestamp": (
                records[-1].get("timestamp") if records else None
            ),
        }
