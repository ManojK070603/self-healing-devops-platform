
from flask import Flask

from app.monitoring.history_store import MonitoringHistoryStore
from app.monitoring.metrics_service import MonitoringMetricsService
from app.monitoring.monitoring_factory import create_monitor_runner
from app.recovery.docker_recovery_action import DockerRecoveryAction
from app.recovery.recovery_coordinator import RecoveryCoordinator
from app.recovery.recovery_policy import RecoveryPolicy


def create_app(config=None):
    app = Flask(__name__)

    # Recovery is disabled unless explicitly enabled.
    app.config.update(
        RECOVERY_ENABLED=False,
        RECOVERY_ALLOWED_CONTAINERS={},
    )

    if config:
        app.config.update(config)

    recovery_coordinator = None

    if app.config["RECOVERY_ENABLED"]:
        allowed_containers = app.config["RECOVERY_ALLOWED_CONTAINERS"]

        if not allowed_containers:
            raise ValueError(
                "Recovery requires an explicit container allowlist"
            )

        recovery_policy = RecoveryPolicy(
            enabled=True,
            max_attempts=3,
            cooldown_seconds=60,
        )

        recovery_action = DockerRecoveryAction(
            allowed_containers=allowed_containers,
        )

        recovery_coordinator = RecoveryCoordinator(
            recovery_policy,
            recovery_action,
        )

        app.extensions["recovery_policy"] = recovery_policy
        app.extensions["recovery_coordinator"] = recovery_coordinator

    history_store = MonitoringHistoryStore()
    metrics_service = MonitoringMetricsService(history_store)

    monitor_runner = create_monitor_runner(
        history_store=history_store,
        service_configs=[
            {
                "name": "platform-api",
                "url": "http://127.0.0.1:5000/health",
            }
        ],
        interval_seconds=30,
        recovery_coordinator=recovery_coordinator,
    )

    app.extensions["monitoring_history_store"] = history_store
    app.extensions["monitoring_metrics_service"] = metrics_service
    app.extensions["monitor_runner"] = monitor_runner

    from app.routes import main
    app.register_blueprint(main)

    return app
