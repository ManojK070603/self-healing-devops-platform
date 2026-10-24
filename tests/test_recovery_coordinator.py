from unittest.mock import Mock

from app.recovery.recovery_coordinator import RecoveryCoordinator
from app.recovery.recovery_policy import RecoveryPolicy


def test_disabled_policy_blocks_recovery():
    action = Mock(return_value=True)
    policy = RecoveryPolicy(enabled=False)
    coordinator = RecoveryCoordinator(policy, action)

    result = coordinator.attempt_recovery("demo-service")

    assert result["attempted"] is False
    action.assert_not_called()


def test_allowed_recovery_calls_action():
    action = Mock(return_value=True)
    policy = RecoveryPolicy(
        enabled=True,
        max_attempts=3,
        cooldown_seconds=60,
    )
    coordinator = RecoveryCoordinator(policy, action)

    result = coordinator.attempt_recovery("demo-service")

    assert result["attempted"] is True
    assert result["success"] is True
    action.assert_called_once_with("demo-service")


def test_failed_action_consumes_attempt():
    action = Mock(return_value=False)
    policy = RecoveryPolicy(
        enabled=True,
        max_attempts=3,
        cooldown_seconds=0,
    )
    coordinator = RecoveryCoordinator(policy, action)

    result = coordinator.attempt_recovery("demo-service")

    assert result["attempted"] is True
    assert result["success"] is False
    assert policy.attempts == 1


def test_action_exception_is_handled():
    action = Mock(side_effect=RuntimeError("simulated failure"))
    policy = RecoveryPolicy(
        enabled=True,
        cooldown_seconds=0,
    )
    coordinator = RecoveryCoordinator(policy, action)

    result = coordinator.attempt_recovery("demo-service")

    assert result["attempted"] is True
    assert result["success"] is False
    assert "simulated failure" in result["message"]
    assert policy.attempts == 1


def test_maximum_attempts_block_further_actions():
    action = Mock(return_value=True)
    policy = RecoveryPolicy(
        enabled=True,
        max_attempts=1,
        cooldown_seconds=0,
    )
    coordinator = RecoveryCoordinator(policy, action)

    first = coordinator.attempt_recovery("demo-service")
    second = coordinator.attempt_recovery("demo-service")

    assert first["success"] is True
    assert second["attempted"] is False
    assert action.call_count == 1
