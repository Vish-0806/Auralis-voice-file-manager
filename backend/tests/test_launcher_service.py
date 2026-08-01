"""Unit tests for LauncherService (Phase 11.3)."""

import sys
# pyrefly: ignore [missing-import]
import pytest

from brain.os.application import (
    ApplicationLaunchRequest,
    ApplicationLaunchResult,
    ApplicationNotFoundError,
    LauncherService,
)


def test_launcher_service_launch_python() -> None:
    launcher = LauncherService()

    # Launch python -c "print('hello')"
    req = ApplicationLaunchRequest(
        app_id_or_name=sys.executable,
        arguments=["-c", "print('hello')"],
    )

    res = launcher.launch(req)
    assert isinstance(res, ApplicationLaunchResult)
    assert res.success is True
    assert res.process_id is not None and res.process_id > 0


def test_launcher_service_launch_invalid_target() -> None:
    launcher = LauncherService()

    req = ApplicationLaunchRequest(app_id_or_name="non_existent_app_executable_12345")
    with pytest.raises(ApplicationNotFoundError):
        launcher.launch(req)
