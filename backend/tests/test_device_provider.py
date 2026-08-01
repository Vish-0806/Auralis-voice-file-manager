"""Unit tests for DeviceProvider (Phase 11.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.device import (
    DeviceCapabilities,
    DeviceHealth,
    DeviceProvider,
    DeviceStatistics,
    IDeviceController,
    IDeviceDetector,
    IDeviceMonitor,
    IDeviceService,
)


def test_device_provider_getters_and_health() -> None:
    provider = DeviceProvider()

    assert isinstance(provider.get_detector(), IDeviceDetector)
    assert isinstance(provider.get_service(), IDeviceService)
    assert isinstance(provider.get_controller(), IDeviceController)
    assert isinstance(provider.get_monitor(), IDeviceMonitor)

    health = provider.get_health()
    assert isinstance(health, DeviceHealth)
    assert health.healthy is True
    assert health.status == "READY"

    stats = provider.get_statistics()
    assert isinstance(stats, DeviceStatistics)

    caps = provider.get_capabilities()
    assert isinstance(caps, DeviceCapabilities)
    assert caps.supports_volume_control is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "DeviceProvider"
