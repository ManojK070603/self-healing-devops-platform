
import time
import urllib.error
import urllib.request


def check_http_health(url, timeout=3):
    """Check whether an HTTP service responds successfully."""
    started_at = time.monotonic()

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "self-healing-monitor/1.0"},
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            elapsed = time.monotonic() - started_at

            return {
                "healthy": 200 <= response.status < 400,
                "status_code": response.status,
                "response_time_ms": round(elapsed * 1000, 2),
                "error": None,
            }

    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        elapsed = time.monotonic() - started_at

        return {
            "healthy": False,
            "status_code": None,
            "response_time_ms": round(elapsed * 1000, 2),
            "error": str(exc),
        }

class HealthMonitor:
    """Track consecutive health-check failures for one service."""

    def __init__(self, failure_threshold=3):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")

        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0
        self.last_result = None

    def record_result(self, result):
        self.last_result = result

        if result["healthy"]:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

        return {
            "healthy": (
                result["healthy"]
                and self.consecutive_failures == 0
            ),
            "consecutive_failures": self.consecutive_failures,
            "threshold": self.failure_threshold,
            "unhealthy": (
                self.consecutive_failures >= self.failure_threshold
            ),
            "last_result": self.last_result,
        }
