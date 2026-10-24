import pytest

from app.recovery.recovery_policy import RecoveryPolicy


def test_recovery_is_disabled_by_default():
    policy = RecoveryPolicy()

    assert policy.can_attempt_recovery(now=100) is False


def test_enabled_policy_allows_first_attempt():
    policy = RecoveryPolicy(
        enabled=True,
        max_attempts=3,
        cooldown_seconds=60,
    )

    assert policy.can_attempt_recovery(now=100) is True
    assert policy.record_attempt(now=100) is True
    assert policy.attempts == 1


def test_cooldown_blocks_immediate_retry():
    policy = RecoveryPolicy(
        enabled=True,
        cooldown_seconds=60,
    )

    assert policy.record_attempt(now=100) is True
    assert policy.can_attempt_recovery(now=120) is False
    assert policy.can_attempt_recovery(now=160) is True


def test_maximum_attempts_are_enforced():
    policy = RecoveryPolicy(
        enabled=True,
        max_attempts=2,
        cooldown_seconds=0,
    )

    assert policy.record_attempt(now=100) is True
    assert policy.record_attempt(now=101) is True
    assert policy.record_attempt(now=102) is False
    assert policy.attempts == 2


def test_invalid_max_attempts_are_rejected():
    with pytest.raises(ValueError):
        RecoveryPolicy(max_attempts=0)


def test_negative_cooldown_is_rejected():
    with pytest.raises(ValueError):
        RecoveryPolicy(cooldown_seconds=-1)