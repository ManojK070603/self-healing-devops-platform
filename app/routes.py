from flask import Blueprint, jsonify

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Self-Healing Devops Platform",
        "status": "running",
        "message": "Welcome to the platform API"
    }), 200


@main.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200