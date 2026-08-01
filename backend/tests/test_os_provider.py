"""Unit tests for OperatingSystemProvider (Phase 11.1)."""

from brain.os import (
    EnvironmentSnapshot,
    IPathService,
    OperatingSystemInfo,
    OperatingSystemProvider,
    ProviderHealth,
)


def test_os_provider_initialization_and_methods() -> None:
    provider = OperatingSystemProvider()

    assert provider.is_available() is True

    plat_info = provider.get_platform_info()
    assert isinstance(plat_info, OperatingSystemInfo)

    env_snap = provider.get_environment_snapshot()
    assert isinstance(env_snap, EnvironmentSnapshot)

    path_svc = provider.get_path_service()
    assert isinstance(path_svc, IPathService)

    health = provider.get_health()
    assert isinstance(health, ProviderHealth)
    assert health.healthy is True
    assert health.status == "READY"

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "OperatingSystemProvider"
    assert diag["available"] is True


def test_os_provider_availability_toggle() -> None:
    provider = OperatingSystemProvider()
    assert provider.is_available() is True

    provider.set_availability(False)
    assert provider.is_available() is False

    health = provider.get_health()
    assert health.healthy is False
    assert health.status == "UNAVAILABLE"
