"""Unit tests for Phase 11.1 Operating System Abstraction Layer models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os import (
    Architecture,
    EnvironmentSnapshot,
    OperatingSystem,
    OperatingSystemInfo,
    OSRuntimeStatus,
    PathInformation,
    PlatformArchitecture,
    ProviderConfiguration,
    ProviderHealth,
    RuntimeState,
    RuntimeStatistics,
)


def test_enums_values() -> None:
    assert OperatingSystem.WINDOWS.value == "Windows"
    assert OperatingSystem.LINUX.value == "Linux"
    assert OperatingSystem.MACOS.value == "macOS"
    assert OperatingSystem.UNKNOWN.value == "Unknown"

    assert Architecture.X64.value == "x64"
    assert Architecture.X86.value == "x86"
    assert Architecture.ARM.value == "ARM"
    assert Architecture.ARM64.value == "ARM64"
    assert Architecture.UNKNOWN.value == "Unknown"

    assert RuntimeState.INITIALIZING.value == "Initializing"
    assert RuntimeState.RUNNING.value == "Running"
    assert RuntimeState.STOPPING.value == "Stopping"
    assert RuntimeState.STOPPED.value == "Stopped"
    assert RuntimeState.FAILED.value == "Failed"


def test_operating_system_info_defaults_and_immutability() -> None:
    info = OperatingSystemInfo()
    assert info.operating_system == OperatingSystem.UNKNOWN
    assert info.architecture == Architecture.UNKNOWN
    assert info.hostname == ""

    info_custom = OperatingSystemInfo(
        operating_system=OperatingSystem.WINDOWS,
        architecture=Architecture.X64,
        hostname="my-host",
    )
    assert info_custom.operating_system == OperatingSystem.WINDOWS
    assert info_custom.hostname == "my-host"

    with pytest.raises((TypeError, ValidationError)):
        info_custom.hostname = "new-host"  # type: ignore


def test_platform_architecture_defaults_and_immutability() -> None:
    arch = PlatformArchitecture()
    assert arch.architecture == Architecture.UNKNOWN
    assert arch.pointer_bitness == 64
    assert arch.is_64bit is True
    assert arch.endianness == "little"

    with pytest.raises((TypeError, ValidationError)):
        arch.pointer_bitness = 32  # type: ignore


def test_environment_snapshot_defaults_and_immutability() -> None:
    snap = EnvironmentSnapshot(
        home_directory="/home/user",
        username="testuser",
        process_id=1234,
    )
    assert snap.home_directory == "/home/user"
    assert snap.username == "testuser"
    assert snap.process_id == 1234
    assert isinstance(snap.captured_at, datetime)

    with pytest.raises((TypeError, ValidationError)):
        snap.username = "otheruser"  # type: ignore


def test_path_information_defaults_and_immutability() -> None:
    info = PathInformation(original_path="/tmp/foo.txt", is_absolute=True)
    assert info.original_path == "/tmp/foo.txt"
    assert info.is_absolute is True

    with pytest.raises((TypeError, ValidationError)):
        info.original_path = "/tmp/bar.txt"  # type: ignore


def test_runtime_statistics_defaults_and_immutability() -> None:
    stats = RuntimeStatistics(total_requests=10, platform_checks=5)
    assert stats.total_requests == 10
    assert stats.platform_checks == 5

    with pytest.raises((TypeError, ValidationError)):
        stats.total_requests = 20  # type: ignore


def test_provider_health_defaults_and_immutability() -> None:
    health = ProviderHealth(healthy=True, status="READY")
    assert health.healthy is True
    assert health.status == "READY"

    with pytest.raises((TypeError, ValidationError)):
        health.healthy = False  # type: ignore


def test_os_runtime_status_defaults_and_immutability() -> None:
    status = OSRuntimeStatus(state=RuntimeState.RUNNING, healthy=True)
    assert status.state == RuntimeState.RUNNING
    assert status.healthy is True

    with pytest.raises((TypeError, ValidationError)):
        status.state = RuntimeState.STOPPED  # type: ignore


def test_provider_configuration_defaults_and_immutability() -> None:
    config = ProviderConfiguration(strict_path_validation=True)
    assert config.enable_cache is True
    assert config.strict_path_validation is True

    with pytest.raises((TypeError, ValidationError)):
        config.enable_cache = False  # type: ignore
