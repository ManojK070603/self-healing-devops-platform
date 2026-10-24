
from datetime import datetime, timezone


class IncidentManager:
    """Store incidents created by the monitoring engine."""

    def __init__(self):
        self.incidents = []
        self.next_id = 1

    def create_incident(self, service, reason):
        incident = {
            "id": self.next_id,
            "service": service,
            "reason": reason,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.incidents.append(incident)
        self.next_id += 1

        return incident

    
    def resolve_incident(self, incident_id):
        """Mark an existing open incident as resolved."""
        for incident in self.incidents:
            if incident["id"] == incident_id:
                if incident["status"] == "open":
                    incident["status"] = "resolved"
                    incident["resolved_at"] = (
                        datetime.now(timezone.utc).isoformat()
                    )
                return incident

        return None

    def list_incidents(self):
        return list(self.incidents)
