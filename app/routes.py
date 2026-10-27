from flask import Blueprint, current_app, jsonify, request

from app.demo_data import (
    DEMO_SERVICES,
    DEMO_DEPLOYMENTS,
    DEMO_INCIDENTS,
    DEMO_METRICS,
    DEMO_SECURITY_SCANS,
)

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Self-Healing DevOps Platform",
        "status": "running",
        "message": "Welcome to the platform API"
    }), 200


@main.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200


@main.route("/api/dashboard", methods=["GET"])
def dashboard():
    healthy_services = sum(
        service["status"] == "healthy"
        for service in DEMO_SERVICES
    )

    active_incidents = sum(
        incident["status"] in ["open", "investigating"]
        for incident in DEMO_INCIDENTS
    )

    resolved_incidents = sum(
        incident["status"] == "resolved"
        for incident in DEMO_INCIDENTS
    )

    successful_deployments = sum(
        deployment["status"] == "success"
        for deployment in DEMO_DEPLOYMENTS
    )

    active_deployments = sum(
        deployment["status"] == "in_progress"
        for deployment in DEMO_DEPLOYMENTS
    )

    total_findings = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for scan in DEMO_SECURITY_SCANS:
        for severity, count in scan["findings"].items():
            total_findings[severity] += count

    return jsonify({
        "platform": "Self-Healing DevOps Platform",
        "status": "operational",
        "demo_data": True,
        "services": {
            "total": len(DEMO_SERVICES),
            "healthy": healthy_services,
            "unhealthy": len(DEMO_SERVICES) - healthy_services
        },
        "incidents": {
            "total": len(DEMO_INCIDENTS),
            "active": active_incidents,
            "resolved": resolved_incidents
        },
        "deployments": {
            "total": len(DEMO_DEPLOYMENTS),
            "successful": successful_deployments,
            "in_progress": active_deployments
        },
        "security": {
            "total_scans": len(DEMO_SECURITY_SCANS),
            "findings": total_findings
        },
        "self_healing": {
            "enabled": False,
            "recoveries_today": 0
        }
    }), 200


@main.route("/api/deployments", methods=["GET"])
def deployments():
    return jsonify({
        "demo_data": True,
        "total": len(DEMO_DEPLOYMENTS),
        "deployments": DEMO_DEPLOYMENTS
    }), 200


@main.route("/api/incidents", methods=["GET"])
def incidents():
    return jsonify({
        "demo_data": True,
        "total": len(DEMO_INCIDENTS),
        "incidents": DEMO_INCIDENTS
    }), 200


@main.route("/api/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "demo_data": True,
        "metrics": DEMO_METRICS
    }), 200


@main.route("/api/security-scans", methods=["GET"])
def security_scans():
    return jsonify({
        "demo_data": True,
        "total": len(DEMO_SECURITY_SCANS),
        "scans": DEMO_SECURITY_SCANS
    }), 200

@main.route("/api/monitoring/metrics", methods=["GET"])
def monitoring_metrics():
    service_name = request.args.get("service")

    metrics_service = current_app.extensions[
        "monitoring_metrics_service"
    ]

    return jsonify({
        "demo_data": False,
        "service": service_name,
        "metrics": metrics_service.get_metrics(service_name),
    }), 200

@main.route("/api/dashboard/live", methods=["GET"])
def live_dashboard():
    history_store = current_app.extensions[
        "monitoring_history_store"
    ]
    metrics_service = current_app.extensions[
        "monitoring_metrics_service"
    ]

    service_names = history_store.get_service_names()
    service_statuses = []

    for service_name in service_names:
        latest = history_store.get_latest(service_name)

        if latest is None:
            continue

        service_statuses.append({
            "name": service_name,
            "status": (
                "healthy" if latest["healthy"] else "unhealthy"
            ),
            "status_code": latest.get("status_code"),
            "response_time_ms": latest.get("response_time_ms"),
            "last_checked": latest.get("timestamp"),
            "error": latest.get("error"),
        })

    healthy_count = sum(
        service["status"] == "healthy"
        for service in service_statuses
    )

    return jsonify({
        "platform": "Self-Healing DevOps Platform",
        "demo_data": False,
        "services": {
            "total": len(service_statuses),
            "healthy": healthy_count,
            "unhealthy": len(service_statuses) - healthy_count,
            "items": service_statuses,
        },
        "metrics": metrics_service.get_metrics(),
    }), 200

@main.route("/api/monitoring/check", methods=["POST"])
def run_monitoring_check():
    runner = current_app.extensions["monitor_runner"]
    results = runner.run_once()

    return jsonify({
        "demo_data": False,
        "results": results,
    }), 200