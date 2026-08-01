"""Unit tests for ProcessProvider (Phase 11.4)."""

# pyrefly: ignore [missing-import]
import pytest

from brain.os.process import (
    IProcessController,
    IProcessDetector,
    IProcessMonitor,
    IProcessService,
    ProcessCapabilities,
    ProcessHealth,
    ProcessProvider,
    ProcessStatistics,
)


def test_process_provider_getters_and_health() -> None:
    provider = ProcessProvider()

    assert isinstance(provider.get_detector(), IProcessDetector)
    assert isinstance(provider.get_service(), IProcessService)
    assert isinstance(provider.get_monitor(), IProcessMonitor)
    assert isinstance(provider.get_controller(), IProcessController)

    health = provider.get_health()
    assert isinstance(health, ProcessHealth)
    assert health.healthy is True
    assert health.status == "READY"

    stats = provider.get_statistics()
    assert isinstance(stats, ProcessStatistics)

    caps = provider.get_capabilities()
    assert isinstance(caps, ProcessCapabilities)
    assert caps.supports_tree_termination is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "ProcessProvider"
