import subprocess


class DockerRecoveryAction:
    """Restart only Docker containers explicitly approved for recovery."""

    def __init__(self, allowed_containers, timeout_seconds=15):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.allowed_containers = dict(allowed_containers)
        self.timeout_seconds = timeout_seconds

    def __call__(self, service_name):
        container_name = self.allowed_containers.get(service_name)

        # Reject services that aren't explicitly approved.
        if not container_name:
            return False

        result = subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )

        return result.returncode == 0
