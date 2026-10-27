
from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock


class MonitoringHistoryStore:
    """Store a bounded history of health-check results per service."""

    def get_service_names(self):
        """Return the names of services with recorded history."""
        with self._lock:
            return list(self._history.keys())

    def __init__(self, max_records=100):
        if max_records < 1:
            raise ValueError("max_records must be at least 1")

        self.max_records = max_records
        self._history = defaultdict(
            lambda: deque(maxlen=max_records)
        )
        self._lock = Lock()

    def record(self, result):
        """Record a health-check result and return a copy."""
        if not isinstance(result, dict):
            raise TypeError("result must be a dictionary")

        if not result.get("service"):
            raise ValueError("result must include a service name")

        entry = deepcopy(result)
        entry.setdefault(
            "timestamp",
            datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._history[entry["service"]].append(entry)

        return deepcopy(entry)

    def get_history(self, service_name):
        """Return a copy of the stored history, oldest first."""
        with self._lock:
            return deepcopy(list(self._history.get(service_name, [])))

    def get_latest(self, service_name):
        """Return the latest result, or None if no history exists."""
        with self._lock:
            history = self._history.get(service_name)

            if not history:
                return None

            return deepcopy(history[-1])
