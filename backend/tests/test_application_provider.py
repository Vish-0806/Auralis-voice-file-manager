"""Unit tests for ApplicationProvider (Phase 11.3)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.application import (
    ApplicationCapabilities,
    ApplicationHealth,
    ApplicationProvider,
    ApplicationStatistics,
    IApplicationDetector,
    IApplicationMonitor,
    IApplicationRegistry,
    ILauncherService,
)


def test_application_provider_getters_and_health() -> None:
    provider = ApplicationProvider()

    assert isinstance(provider.get_registry(), IApplicationRegistry)
    assert isinstance(provider.get_detector(), IApplicationDetector)
    assert isinstance(provider.get_launcher(), ILauncherService)
    assert isinstance(provider.get_monitor(), IApplicationMonitor)

    health = provider.get_health()
    assert isinstance(health, ApplicationHealth)
    assert health.healthy is True
    assert health.status == "READY"

    stats = provider.get_statistics()
    assert isinstance(stats, ApplicationStatistics)

    caps = provider.get_capabilities()
    assert isinstance(caps, ApplicationCapabilities)
    assert caps.supports_discovery is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "ApplicationProvider"
