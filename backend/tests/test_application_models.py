"""Unit tests for Phase 11.3 Application Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.application import (
    ApplicationCapabilities,
    ApplicationHealth,
    ApplicationInfo,
    ApplicationLaunchRequest,
    ApplicationLaunchResult,
    ApplicationRegistryEntry,
    ApplicationRuntimeStatus,
    ApplicationState,
    ApplicationStatistics,
    InstalledApplication,
    LaunchMode,
    RunningApplication,
    VisibilityMode,
)


def test_application_enums() -> None:
    assert ApplicationState.INSTALLED.value == "installed"
    assert ApplicationState.RUNNING.value == "running"

    assert LaunchMode.NORMAL.value == "normal"
    assert LaunchMode.BACKGROUND.value == "background"

    assert VisibilityMode.VISIBLE.value == "visible"
    assert VisibilityMode.HIDDEN.value == "hidden"


def test_application_info_defaults_and_immutability() -> None:
    info = ApplicationInfo(name="Calculator", executable_path="calc.exe")
    assert info.name == "Calculator"
    assert info.executable_path == "calc.exe"
    assert info.category == "General"

    with pytest.raises((TypeError, ValidationError)):
        info.name = "Other"  # type: ignore


def test_installed_application_defaults_and_immutability() -> None:
    info = ApplicationInfo(name="Notepad")
    app = InstalledApplication(info=info, install_path="/bin/notepad")
    assert app.info.name == "Notepad"
    assert app.install_path == "/bin/notepad"

    with pytest.raises((TypeError, ValidationError)):
        app.install_path = "/other/path"  # type: ignore


def test_running_application_defaults_and_immutability() -> None:
    app = RunningApplication(process_id=4321, name="python")
    assert app.process_id == 4321
    assert app.state == ApplicationState.RUNNING

    with pytest.raises((TypeError, ValidationError)):
        app.process_id = 9999  # type: ignore


def test_application_launch_request_defaults_and_immutability() -> None:
    req = ApplicationLaunchRequest(app_id_or_name="calc")
    assert req.app_id_or_name == "calc"
    assert req.launch_mode == LaunchMode.NORMAL

    with pytest.raises((TypeError, ValidationError)):
        req.app_id_or_name = "notepad"  # type: ignore


def test_application_launch_result_defaults_and_immutability() -> None:
    res = ApplicationLaunchResult(success=True, process_id=100)
    assert res.success is True
    assert res.process_id == 100

    with pytest.raises((TypeError, ValidationError)):
        res.success = False  # type: ignore
