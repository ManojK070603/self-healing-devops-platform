import logging
import threading

logger = logging.getLogger(__name__)


class MonitorRunner:
    """Run health checks repeatedly until stopped."""

    def __init__(self, monitored_services, interval_seconds=30):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")

        if not monitored_services:
            raise ValueError("At least one monitored service is required")

        self.monitored_services = list(monitored_services)
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def run_once(self):
        """Check each configured service once."""
        results = []

        for service in self.monitored_services:
            try:
                result = service.check_once()
                results.append(result)
            except Exception:
                logger.exception(
                    "Monitoring failed for service %s",
                    service.name,
                )
                results.append({
                    "service": service.name,
                    "error": "Monitoring check failed; see logs",
                })

        return results

    def start(self):
        """Start monitoring in a background thread."""
        if self.is_running:
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="self-healing-monitor",
            daemon=True,
        )
        self._thread.start()
        return True

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.run_once()

            if self._stop_event.wait(self.interval_seconds):
                break

    def stop(self, timeout=5):
        """Request shutdown and wait briefly for the worker."""
        self._stop_event.set()

        if self._thread is not None:
            if self._thread is threading.current_thread():
                return True

            self._thread.join(timeout=timeout)

            if self._thread.is_alive():
                return False

            self._thread = None

        return True