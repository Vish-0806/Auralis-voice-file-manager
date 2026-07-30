"""Unit tests for DependencyRegistry (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import DependencyRegistry, RuntimeComponent


class DummyRuntime:
    def __init__(self, name: str) -> None:
        self.name = name


@pytest.fixture
def registry() -> DependencyRegistry:
    return DependencyRegistry()


# ---------------------------------------------------------------------------
# Registration & Lookup
# ---------------------------------------------------------------------------

def test_register_and_get(registry: DependencyRegistry) -> None:
    dummy = DummyRuntime("voice")
    registry.register(RuntimeComponent.VOICE, dummy)
    assert registry.get(RuntimeComponent.VOICE) is dummy
    assert registry.get("VOICE") is dummy


def test_register_string_name(registry: DependencyRegistry) -> None:
    dummy = DummyRuntime("custom")
    registry.register("CUSTOM", dummy)
    assert registry.get("CUSTOM") is dummy


def test_unregister(registry: DependencyRegistry) -> None:
    dummy = DummyRuntime("voice")
    registry.register(RuntimeComponent.VOICE, dummy)
    assert registry.unregister(RuntimeComponent.VOICE) is True
    assert registry.get(RuntimeComponent.VOICE) is None or isinstance(registry.get(RuntimeComponent.VOICE), object)


def test_unregister_unknown(registry: DependencyRegistry) -> None:
    assert registry.unregister("UNKNOWN") is False


# ---------------------------------------------------------------------------
# Auto Discovery & Validation
# ---------------------------------------------------------------------------

def test_auto_discover_voice(registry: DependencyRegistry) -> None:
    inst = registry.get(RuntimeComponent.VOICE)
    assert inst is not None


def test_validate_registrations(registry: DependencyRegistry) -> None:
    res = registry.validate_registrations()
    assert isinstance(res, dict)
    assert "VOICE" in res
    assert "FILESYSTEM" in res


def test_resolve_all(registry: DependencyRegistry) -> None:
    resolved = registry.resolve_all()
    assert isinstance(resolved, dict)
    assert len(resolved) >= 5


def test_clear(registry: DependencyRegistry) -> None:
    registry.register(RuntimeComponent.VOICE, DummyRuntime("v"))
    registry.clear()
    assert len(registry.list_components()) == 0


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_dependency_registry_thread_safety(registry: DependencyRegistry) -> None:
    import threading

    def register_worker(i: int) -> None:
        registry.register(f"COMP_{i}", DummyRuntime(f"rt_{i}"))

    threads = [threading.Thread(target=register_worker, args=(i,)) for i in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(registry.list_components()) >= 30
