"""Unit tests for PathService (Phase 11.1)."""

from brain.os import (
    EnvironmentService,
    OperatingSystem,
    PathInformation,
    PathService,
)


def test_path_normalization_linux_macos() -> None:
    path_svc = PathService()

    norm_linux = path_svc.normalize_path("/foo/bar/../baz/./file.txt", target_os=OperatingSystem.LINUX)
    assert norm_linux == "/foo/baz/file.txt"

    norm_macos = path_svc.normalize_path("/Users/test/./docs/../file.png", target_os=OperatingSystem.MACOS)
    assert norm_macos == "/Users/test/file.png"


def test_path_normalization_windows() -> None:
    path_svc = PathService()

    norm_win = path_svc.normalize_path("C:\\foo\\bar\\..\\baz\\file.txt", target_os=OperatingSystem.WINDOWS)
    assert norm_win == "C:\\foo\\baz\\file.txt"

    norm_win_slashes = path_svc.normalize_path("C:/foo/bar/../baz/file.txt", target_os=OperatingSystem.WINDOWS)
    assert norm_win_slashes == "C:\\foo\\baz\\file.txt"


def test_expand_user() -> None:
    env_svc = EnvironmentService(home_override="/home/auralis")
    path_svc = PathService(environment_service=env_svc)

    expanded_tilde = path_svc.expand_user("~")
    assert expanded_tilde == "/home/auralis"

    expanded_path = path_svc.expand_user("~/documents/file.txt")
    assert "/home/auralis" in expanded_path


def test_expand_env_vars() -> None:
    env_svc = EnvironmentService(env_overrides={"MY_VAR": "auralis_val", "WIN_VAR": "win_val"})
    path_svc = PathService(environment_service=env_svc)

    exp_unix = path_svc.expand_vars("/path/$MY_VAR/file.txt")
    assert exp_unix == "/path/auralis_val/file.txt"

    exp_unix_curly = path_svc.expand_vars("/path/${MY_VAR}/file.txt")
    assert exp_unix_curly == "/path/auralis_val/file.txt"

    exp_win = path_svc.expand_vars("C:\\path\\%WIN_VAR%\\file.txt")
    assert exp_win == "C:\\path\\win_val\\file.txt"


def test_resolve_absolute() -> None:
    env_svc = EnvironmentService(cwd_override="/workspace/project")
    path_svc = PathService(environment_service=env_svc)

    resolved_rel = path_svc.resolve_absolute("subfolder/file.txt", base_dir="/workspace/project")
    assert "workspace" in resolved_rel and "file.txt" in resolved_rel


def test_is_safe_path() -> None:
    env_svc = EnvironmentService(cwd_override="/workspace/app")
    path_svc = PathService(environment_service=env_svc)

    assert path_svc.is_safe_path("/workspace/app/data/file.txt", base_dir="/workspace/app") is True
    assert path_svc.is_safe_path("/workspace/app/../../etc/passwd", base_dir="/workspace/app") is False


def test_compare_paths() -> None:
    path_svc = PathService()

    # Windows case insensitive
    assert path_svc.compare_paths("C:\\FOO\\BAR", "c:\\foo\\bar", target_os=OperatingSystem.WINDOWS) is True

    # Linux case sensitive
    assert path_svc.compare_paths("/foo/bar", "/FOO/BAR", target_os=OperatingSystem.LINUX) is False
    assert path_svc.compare_paths("/foo/bar", "/foo/bar", target_os=OperatingSystem.LINUX) is True


def test_get_path_info() -> None:
    path_svc = PathService()
    info = path_svc.get_path_info("test.txt")

    assert isinstance(info, PathInformation)
    assert info.original_path == "test.txt"
    assert info.extension == ".txt"
    assert isinstance(info.is_safe, bool)
