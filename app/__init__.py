from flask import Flask

from app.monitoring.history_store import MonitoringHistoryStore
from app.monitoring.metrics_service import MonitoringMetricsService
from app.monitoring.monitoring_factory import create_monitor_runner


def create_app():
    app = Flask(__name__)

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
    )

    app.extensions["monitoring_history_store"] = history_store
    app.extensions["monitoring_metrics_service"] = metrics_service
    app.extensions["monitor_runner"] = monitor_runner

    from app.routes import main
    app.register_blueprint(main)

    return app
