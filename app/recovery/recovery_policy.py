import time


class RecoveryPolicy:
    """Decide whether a recovery attempt is allowed."""

    def __init__(
        self,
        enabled=False,
        max_attempts=3,
        cooldown_seconds=60,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")

        self.enabled = enabled
        self.max_attempts = max_attempts
        self.cooldown_seconds = cooldown_seconds

        self.attempts = 0
        self.last_attempt_at = None

    def can_attempt_recovery(self, now=None):
        """Return whether another recovery attempt is permitted."""
        if not self.enabled:
            return False

        if self.attempts >= self.max_attempts:
            return False

        current_time = time.monotonic() if now is None else now

        if self.last_attempt_at is not None:
            elapsed = current_time - self.last_attempt_at

            if elapsed < self.cooldown_seconds:
                return False

        return True

    def record_attempt(self, now=None):
        """Record an attempt only when policy permits it."""
        if not self.can_attempt_recovery(now=now):
            return False

        current_time = time.monotonic() if now is None else now

        self.attempts += 1
        self.last_attempt_at = current_time

        return True