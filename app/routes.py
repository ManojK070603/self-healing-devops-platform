from flask import Blueprint, jsonify

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
    return jsonify({
        "platform": "Self-Healing DevOps Platform",
        "status": "operational",
        "demo_data": True,
        "services": {
            "total": 1,
            "healthy": 1,
            "unhealthy": 0
        },
        "incidents": {
            "total": 0,
            "active": 0,
            "resolved": 0
        },
        "self_healing": {
            "enabled": False,
            "recoveries_today": 0
        }
    }), 200