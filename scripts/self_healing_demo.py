
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.monitoring.health_checker import check_http_health
from app.monitoring.incident_manager import IncidentManager
from app.monitoring.monitor_service import MonitoredService
from app.recovery.docker_recovery_action import DockerRecoveryAction
from app.recovery.recovery_coordinator import RecoveryCoordinator
from app.recovery.recovery_policy import RecoveryPolicy


def main():
    service_name = "demo-nginx"
    container_name = "self-healing-test-container"
    health_url = "http://127.0.0.1:8088/"

    # Confirm the dedicated test container exists and is running.
    inspect = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
        capture_output=True,
        text=True,
        check=True,
    )

    if inspect.stdout.strip() != "true":
        raise RuntimeError(
            f"{container_name} is not running. Start it with "
            f"'docker start {container_name}' and retry."
        )

    initial_health = check_http_health(health_url, timeout=3)
    if not initial_health["healthy"]:
        raise RuntimeError(
            f"Test service is not healthy before the demo: "
            f"{initial_health}"
        )

    recovery_action = DockerRecoveryAction({
        service_name: container_name,
    })

    recovery_policy = RecoveryPolicy(
        enabled=True,
        max_attempts=1,
        cooldown_seconds=0,
    )

    coordinator = RecoveryCoordinator(
        recovery_policy,
        recovery_action,
    )

    incident_manager = IncidentManager()

    service = MonitoredService(
        name=service_name,
        url=health_url,
        incident_manager=incident_manager,
        failure_threshold=3,
        timeout=2,
        recovery_coordinator=coordinator,
        recovery_verification_attempts=10,
        recovery_verification_interval=1,
    )

    print("1. Initial health check passed.")
    print("2. Stopping the dedicated test container...")

    subprocess.run(
        ["docker", "stop", container_name],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )

    print("3. Running three health checks and triggering recovery...")

    result = None
    for attempt in range(3):
        result = service.check_once()
        print(
            f"   Check {attempt + 1}: "
            f"healthy={result['health']['healthy']}, "
            f"consecutive_failures="
            f"{result['health']['consecutive_failures']}"
        )

        if attempt < 2 and result["recovery"] is None:
            time.sleep(0.5)

    print("\n4. Recovery action:")
    print(result["recovery"])

    print("\n5. Recovery verification:")
    print(result["recovery_verification"])

    print("\n6. Incident state:")
    print(incident_manager.list_incidents())

    if not result["recovery"] or not result["recovery"]["success"]:
        raise RuntimeError("The recovery action did not succeed.")

    if (
        result["recovery_verification"] is None
        or not result["recovery_verification"]["healthy"]
    ):
        raise RuntimeError(
            "Recovery ran, but the service did not become healthy."
        )

    if result["active_incident"] is not None:
        raise RuntimeError(
            "The service is healthy, but its incident remains open."
        )

    print("\nSUCCESS: recovery was verified and the incident resolved.")


if __name__ == "__main__":
    main()
