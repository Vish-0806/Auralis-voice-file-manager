"""Unit tests for ApplicationRegistry (Phase 11.3)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.application import (
    ApplicationInfo,
    ApplicationRegistry,
    InstalledApplication,
)


def test_application_registry_register_and_lookup() -> None:
    reg = ApplicationRegistry()

    info = ApplicationInfo(
        app_id="app_calc",
        name="Calculator",
        executable_path="C:\\Windows\\System32\\calc.exe",
        aliases=["calc", "calculator"],
        category="Utility",
    )
    app = InstalledApplication(info=info)

    entry = reg.register_application(app)
    assert entry.app_id == "app_calc"
    assert entry.name == "Calculator"

    # Lookup by ID
    found_id = reg.get_application("app_calc")
    assert found_id is not None
    assert found_id.info.name == "Calculator"

    # Lookup by name
    found_name = reg.get_application("Calculator")
    assert found_name is not None
    assert found_name.info.app_id == "app_calc"

    # Lookup by alias
    found_alias = reg.get_by_alias("calc")
    assert found_alias is not None
    assert found_alias.info.app_id == "app_calc"

    # Lookup by executable
    found_exec = reg.get_by_executable("C:\\Windows\\System32\\calc.exe")
    assert found_exec is not None
    assert found_exec.info.app_id == "app_calc"


def test_application_registry_list_and_unregister() -> None:
    reg = ApplicationRegistry()

    app1 = InstalledApplication(info=ApplicationInfo(app_id="app1", name="App One", category="Tools"))
    app2 = InstalledApplication(info=ApplicationInfo(app_id="app2", name="App Two", category="Games"))

    reg.register_application(app1)
    reg.register_application(app2)

    all_apps = reg.list_applications()
    assert len(all_apps) == 2

    tools = reg.list_applications(category="Tools")
    assert len(tools) == 1
    assert tools[0].info.app_id == "app1"

    # Unregister
    removed = reg.unregister_application("app1")
    assert removed is True
    assert reg.get_application("app1") is None
    assert len(reg.list_applications()) == 1
