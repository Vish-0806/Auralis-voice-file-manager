"""Unit tests for EnvironmentService (Phase 11.1)."""

from brain.os import EnvironmentService, EnvironmentSnapshot


def test_environment_service_defaults() -> None:
    svc = EnvironmentService()
    home = svc.get_home_directory()
    assert isinstance(home, str) and len(home) > 0

    cwd = svc.get_cwd()
    assert isinstance(cwd, str) and len(cwd) > 0

    temp_dir = svc.get_temp_directory()
    assert isinstance(temp_dir, str) and len(temp_dir) > 0

    env_vars = svc.get_environment_variables()
    assert isinstance(env_vars, dict)

    user = svc.get_username()
    assert isinstance(user, str) and len(user) > 0

    tz = svc.get_timezone()
    assert isinstance(tz, str)

    loc = svc.get_locale()
    assert isinstance(loc, str)

    py_exe = svc.get_python_executable()
    assert isinstance(py_exe, str)

    pid = svc.get_process_id()
    assert isinstance(pid, int) and pid > 0

    snapshot = svc.capture_snapshot()
    assert isinstance(snapshot, EnvironmentSnapshot)
    assert snapshot.home_directory == home
    assert snapshot.current_working_directory == cwd
    assert snapshot.username == user
    assert snapshot.process_id == pid


def test_environment_service_overrides() -> None:
    svc = EnvironmentService(
        env_overrides={"AURALIS_TEST_VAR": "hello_world"},
        home_override="/custom/home",
        cwd_override="/custom/cwd",
        temp_dir_override="/custom/temp",
    )

    assert svc.get_home_directory() == "/custom/home"
    assert svc.get_cwd() == "/custom/cwd"
    assert svc.get_temp_directory() == "/custom/temp"
    assert svc.get_env_var("AURALIS_TEST_VAR") == "hello_world"

    snapshot = svc.capture_snapshot()
    assert snapshot.home_directory == "/custom/home"
    assert snapshot.environment_variables["AURALIS_TEST_VAR"] == "hello_world"
