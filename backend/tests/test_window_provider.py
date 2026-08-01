"""Unit tests for WindowProvider (Phase 11.6)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.window import (
    IWindowController,
    IWindowDetector,
    IWindowMonitor,
    IWindowService,
    WindowCapabilities,
    WindowHealth,
    WindowProvider,
    WindowStatistics,
)


def test_window_provider_getters_and_health() -> None:
    provider = WindowProvider()

    assert isinstance(provider.get_detector(), IWindowDetector)
    assert isinstance(provider.get_service(), IWindowService)
    assert isinstance(provider.get_controller(), IWindowController)
    assert isinstance(provider.get_monitor(), IWindowMonitor)

    health = provider.get_health()
    assert isinstance(health, WindowHealth)
    assert health.healthy is True
    assert health.status == "READY"

    stats = provider.get_statistics()
    assert isinstance(stats, WindowStatistics)

    caps = provider.get_capabilities()
    assert isinstance(caps, WindowCapabilities)
    assert caps.supports_window_manipulation is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "WindowProvider"
