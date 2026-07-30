"""Unit tests for BrainRuntimeCoordinator (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    BrainRequest, BrainResponse, BrainRuntimeCoordinator,
    BrainRuntimeHealth, BrainRuntimeStatus,
    get_brain_runtime, reset_brain_runtime,
)


@pytest.fixture(autouse=True)
def isolate_runtime() -> None:
    reset_brain_runtime()
    yield
    reset_brain_runtime()


@pytest.fixture
def coordinator() -> BrainRuntimeCoordinator:
    c = BrainRuntimeCoordinator()
    c.initialize()
    return c


# ---------------------------------------------------------------------------
# Lifecycle & Singleton Access
# ---------------------------------------------------------------------------

def test_coordinator_initialize(coordinator: BrainRuntimeCoordinator) -> None:
    assert coordinator.status == BrainRuntimeStatus.READY


def test_coordinator_process_request(coordinator: BrainRuntimeCoordinator) -> None:
    res = coordinator.process_request("hello brain")
    assert isinstance(res, BrainResponse)
    assert res.success is True


def test_coordinator_health_check(coordinator: BrainRuntimeCoordinator) -> None:
    h = coordinator.health_check()
    assert isinstance(h, BrainRuntimeHealth)
    assert h.healthy is True


def test_coordinator_get_statistics(coordinator: BrainRuntimeCoordinator) -> None:
    st = coordinator.get_statistics()
    assert st.total_requests == 0


def test_coordinator_list_components(coordinator: BrainRuntimeCoordinator) -> None:
    comps = coordinator.list_components()
    assert isinstance(comps, list)


def test_coordinator_shutdown(coordinator: BrainRuntimeCoordinator) -> None:
    assert coordinator.shutdown() is True
    assert coordinator.status == BrainRuntimeStatus.SHUTDOWN


def test_coordinator_restart(coordinator: BrainRuntimeCoordinator) -> None:
    assert coordinator.restart() is True
    assert coordinator.status == BrainRuntimeStatus.READY


def test_get_brain_runtime_singleton() -> None:
    r1 = get_brain_runtime()
    r2 = get_brain_runtime()
    assert r1 is r2
    assert r1.status == BrainRuntimeStatus.READY


def test_reset_brain_runtime() -> None:
    r1 = get_brain_runtime()
    reset_brain_runtime()
    r2 = get_brain_runtime()
    assert r1 is not r2


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_brain_runtime_thread_safety(coordinator: BrainRuntimeCoordinator) -> None:
    import threading
    results = []

    def worker(i: int) -> None:
        res = coordinator.process_request(f"task_{i}")
        results.append(res)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all(r.success for r in results)
