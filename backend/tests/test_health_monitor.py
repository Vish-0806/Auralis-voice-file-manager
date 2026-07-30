"""Unit tests for HealthMonitor (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    BrainRuntimeHealth, DependencyRegistry, HealthMonitor,
    RuntimeComponent, SubsystemHealth,
)


@pytest.fixture
def registry() -> DependencyRegistry:
    reg = DependencyRegistry()
    # Populate with auto-discovered real runtimes
    reg.resolve_all()
    return reg


@pytest.fixture
def monitor(registry: DependencyRegistry) -> HealthMonitor:
    return HealthMonitor(registry=registry)


# ---------------------------------------------------------------------------
# Health Monitoring
# ---------------------------------------------------------------------------

def test_check_health_returns_snapshot(monitor: HealthMonitor) -> None:
    h = monitor.check_health()
    assert isinstance(h, BrainRuntimeHealth)
    assert h.healthy is True
    assert h.status in ("READY", "DEGRADED")
    assert len(h.subsystems) >= 5


def test_check_subsystem(monitor: HealthMonitor) -> None:
    sh = monitor.check_subsystem(RuntimeComponent.VOICE)
    assert isinstance(sh, SubsystemHealth)
    assert sh.subsystem_name == "VOICE"
    assert sh.healthy is True


def test_is_healthy(monitor: HealthMonitor) -> None:
    assert isinstance(monitor.is_healthy(), bool)


def test_unhealthy_subsystem_detected() -> None:
    reg = DependencyRegistry()
    reg.register(RuntimeComponent.VOICE, None)
    mon = HealthMonitor(registry=reg)
    sh = mon.check_subsystem(RuntimeComponent.VOICE)
    assert sh.healthy is False
    assert sh.status == "MISSING"


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_health_monitor_thread_safety(monitor: HealthMonitor) -> None:
    import threading
    results = []

    def check() -> None:
        results.append(monitor.check_health())

    threads = [threading.Thread(target=check) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all(isinstance(r, BrainRuntimeHealth) for r in results)
