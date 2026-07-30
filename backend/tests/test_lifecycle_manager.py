"""Unit tests for LifecycleManager (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import DependencyRegistry, LifecycleManager, RuntimeComponent


class DummySubsystem:
    def __init__(self, name: str, should_fail: bool = False) -> None:
        self.name = name
        self.initialized = False
        self.shutdown_called = False
        self.cleared = False
        self.should_fail = should_fail

    def initialize(self) -> bool:
        if self.should_fail:
            return False
        self.initialized = True
        return True

    def shutdown(self) -> bool:
        self.shutdown_called = True
        return True

    def clear(self) -> None:
        self.cleared = True


@pytest.fixture
def mock_registry() -> DependencyRegistry:
    reg = DependencyRegistry()
    for comp in RuntimeComponent:
        if comp != RuntimeComponent.BRAIN:
            reg.register(comp, DummySubsystem(comp.value))
    return reg


@pytest.fixture
def lifecycle(mock_registry: DependencyRegistry) -> LifecycleManager:
    return LifecycleManager(registry=mock_registry)


# ---------------------------------------------------------------------------
# Initialization & Shutdown
# ---------------------------------------------------------------------------

def test_initialize_all(lifecycle: LifecycleManager) -> None:
    ok = lifecycle.initialize_all()
    assert ok is True
    status = lifecycle.get_status()
    assert status["FILESYSTEM"] == "READY"
    assert status["VOICE"] == "READY"


def test_initialize_all_with_failing_subsystem(mock_registry: DependencyRegistry) -> None:
    mock_registry.register(RuntimeComponent.PLANNING, DummySubsystem("PLANNING", should_fail=True))
    lm = LifecycleManager(registry=mock_registry)
    ok = lm.initialize_all()
    assert ok is False
    assert lm.get_status()["PLANNING"] == "ERROR"


def test_shutdown_all(lifecycle: LifecycleManager) -> None:
    lifecycle.initialize_all()
    ok = lifecycle.shutdown_all()
    assert ok is True
    status = lifecycle.get_status()
    assert status["FILESYSTEM"] == "SHUTDOWN"
    assert status["VOICE"] == "SHUTDOWN"


def test_restart_all(lifecycle: LifecycleManager) -> None:
    lifecycle.initialize_all()
    ok = lifecycle.restart_all()
    assert ok is True
    status = lifecycle.get_status()
    assert status["FILESYSTEM"] == "READY"


def test_clear_all(lifecycle: LifecycleManager, mock_registry: DependencyRegistry) -> None:
    sub = mock_registry.get(RuntimeComponent.VOICE)
    lifecycle.initialize_all()
    lifecycle.clear_all()
    assert sub.cleared is True


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_lifecycle_manager_thread_safety(lifecycle: LifecycleManager) -> None:
    import threading

    def init_worker() -> None:
        lifecycle.initialize_all()

    threads = [threading.Thread(target=init_worker) for _ in range(15)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert lifecycle.get_status()["FILESYSTEM"] == "READY"
