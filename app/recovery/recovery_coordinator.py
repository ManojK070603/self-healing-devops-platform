class RecoveryCoordinator:
    """Execute recovery actions only when policy permits."""

    def __init__(self, policy, recovery_action):
        self.policy = policy
        self.recovery_action = recovery_action

    def attempt_recovery(self, service_name):
        if not self.policy.can_attempt_recovery():
            return {
                "service": service_name,
                "attempted": False,
                "success": False,
                "message": "Recovery blocked by policy",
            }

        # Consume an attempt before executing the action.
        if not self.policy.record_attempt():
            return {
                "service": service_name,
                "attempted": False,
                "success": False,
                "message": "Recovery blocked by policy",
            }

        try:
            success = bool(self.recovery_action(service_name))
        except Exception as exc:
            return {
                "service": service_name,
                "attempted": True,
                "success": False,
                "message": f"Recovery action failed: {exc}",
            }

        return {
            "service": service_name,
            "attempted": True,
            "success": success,
            "message": (
                "Recovery action completed"
                if success
                else "Recovery action was unsuccessful"
            ),
        }