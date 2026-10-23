DEMO_SERVICES = [
    {
        "name": "self-healing-platform",
        "status": "healthy"
    }
]

DEMO_DEPLOYMENTS = [
    {
        "id": 1,
        "application": "self-healing-platform",
        "version": "v1.0.0",
        "environment": "development",
        "status": "success"
    },
    {
        "id": 2,
        "application": "self-healing-platform",
        "version": "v1.1.0",
        "environment": "staging",
        "status": "in_progress"
    }
]

DEMO_INCIDENTS = [
    {
        "id": 1,
        "title": "API response time elevated",
        "severity": "medium",
        "status": "investigating",
        "service": "self-healing-platform",
        "created_at": "2026-10-22T10:00:00Z"
    },
    {
        "id": 2,
        "title": "Deployment health check failed",
        "severity": "high",
        "status": "open",
        "service": "deployment-service",
        "created_at": "2026-10-22T10:15:00Z"
    },
    {
        "id": 3,
        "title": "Security update completed",
        "severity": "low",
        "status": "resolved",
        "service": "security-service",
        "created_at": "2026-10-22T09:30:00Z"
    }
]

DEMO_METRICS = {
    "cpu_usage_percent": 24.5,
    "memory_usage_percent": 61.2,
    "request_count": 1250,
    "error_rate_percent": 1.6,
    "response_time_ms": 142.8
}

DEMO_SECURITY_SCANS = [
    {
        "id": 1,
        "scanner": "Trivy",
        "status": "completed",
        "findings": {
            "critical": 0,
            "high": 2,
            "medium": 4,
            "low": 3
        },
        "scanned_at": "2026-10-22T10:30:00Z"
    },
    {
        "id": 2,
        "scanner": "Bandit",
        "status": "completed",
        "findings": {
            "critical": 0,
            "high": 0,
            "medium": 1,
            "low": 2
        },
        "scanned_at": "2026-10-22T10:45:00Z"
    }
]