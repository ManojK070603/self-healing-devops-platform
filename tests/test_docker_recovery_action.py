import subprocess
from unittest.mock import Mock, patch

import pytest

from app.recovery.docker_recovery_action import DockerRecoveryAction


def test_approved_service_restarts_its_allowed_container():
    action = DockerRecoveryAction({
        "platform-api": "self-healing-api",
    })

    completed = Mock(returncode=0)

    with patch(
        "app.recovery.docker_recovery_action.subprocess.run",
        return_value=completed,
    ) as run:
        result = action("platform-api")

    assert result is True
    run.assert_called_once_with(
        ["docker", "restart", "self-healing-api"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_unapproved_service_is_rejected():
    action = DockerRecoveryAction({
        "platform-api": "self-healing-api",
    })

    with patch(
        "app.recovery.docker_recovery_action.subprocess.run"
    ) as run:
        result = action("unknown-service")

    assert result is False
    run.assert_not_called()


def test_failed_docker_restart_returns_false():
    action = DockerRecoveryAction({
        "platform-api": "self-healing-api",
    })

    completed = Mock(returncode=1)

    with patch(
        "app.recovery.docker_recovery_action.subprocess.run",
        return_value=completed,
    ):
        result = action("platform-api")

    assert result is False


def test_docker_command_timeout_is_propagated():
    action = DockerRecoveryAction({
        "platform-api": "self-healing-api",
    })

    with patch(
        "app.recovery.docker_recovery_action.subprocess.run",
        side_effect=subprocess.TimeoutExpired("docker", 15),
    ):
        with pytest.raises(subprocess.TimeoutExpired):
            action("platform-api")


def test_timeout_must_be_positive():
    with pytest.raises(ValueError):
        DockerRecoveryAction({}, timeout_seconds=0)
