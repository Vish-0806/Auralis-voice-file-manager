"""Unit tests for DesktopProvider (Phase 11.5)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.desktop import (
    DesktopCapabilities,
    DesktopHealth,
    DesktopProvider,
    DesktopStatistics,
    IClipboardService,
    IDesktopService,
    INotificationService,
)


def test_desktop_provider_getters_and_health() -> None:
    provider = DesktopProvider()

    assert isinstance(provider.get_desktop_service(), IDesktopService)
    assert isinstance(provider.get_clipboard_service(), IClipboardService)
    assert isinstance(provider.get_notification_service(), INotificationService)

    health = provider.get_health()
    assert isinstance(health, DesktopHealth)
    assert health.healthy is True
    assert health.status == "READY"

    stats = provider.get_statistics()
    assert isinstance(stats, DesktopStatistics)
    assert stats.known_folders_count > 0

    caps = provider.get_capabilities()
    assert isinstance(caps, DesktopCapabilities)
    assert caps.supports_known_folders is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "DesktopProvider"
