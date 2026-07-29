"""Unit tests for FilesystemRuntimeCoordinator (Phase 9.5)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.filesystem import (
    FilesystemHealth,
    FilesystemProvider,
    FilesystemRuntimeCoordinator,
    FilesystemRuntimeStatus,
    FilesystemStatistics,
    get_filesystem_runtime,
    reset_filesystem_runtime,
)


@pytest.fixture(autouse=True)
def isolate_runtime() -> None:
    """Reset global singleton before and after every test."""
    reset_filesystem_runtime()
    yield
    reset_filesystem_runtime()


@pytest.fixture
def coordinator() -> FilesystemRuntimeCoordinator:
    c = FilesystemRuntimeCoordinator()
    c.initialize()
    return c


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_initialize_returns_true() -> None:
    c = FilesystemRuntimeCoordinator()
    assert c.initialize() is True


def test_status_is_ready_after_initialize(coordinator: FilesystemRuntimeCoordinator) -> None:
    assert coordinator.status == FilesystemRuntimeStatus.READY


def test_status_is_initializing_before_initialize() -> None:
    c = FilesystemRuntimeCoordinator()
    assert c.status == FilesystemRuntimeStatus.INITIALIZING


def test_double_initialize_is_safe(coordinator: FilesystemRuntimeCoordinator) -> None:
    result = coordinator.initialize()
    assert result is True
    assert coordinator.status == FilesystemRuntimeStatus.READY


def test_initialize_with_existing_provider() -> None:
    provider = FilesystemProvider()
    c = FilesystemRuntimeCoordinator(provider=provider)
    assert c.initialize() is True
    assert c.get_provider() is provider


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------

def test_shutdown_returns_true(coordinator: FilesystemRuntimeCoordinator) -> None:
    assert coordinator.shutdown() is True


def test_status_is_shutdown_after_shutdown(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.shutdown()
    assert coordinator.status == FilesystemRuntimeStatus.SHUTDOWN


def test_get_provider_auto_reinitializes_after_shutdown(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.shutdown()
    provider = coordinator.get_provider()
    assert isinstance(provider, FilesystemProvider)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

def test_health_check_returns_health(coordinator: FilesystemRuntimeCoordinator) -> None:
    health = coordinator.health_check()
    assert isinstance(health, FilesystemHealth)


def test_health_check_healthy_when_ready(coordinator: FilesystemRuntimeCoordinator) -> None:
    health = coordinator.health_check()
    assert health.healthy is True
    assert health.status == "READY"


def test_health_check_unhealthy_after_shutdown(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.shutdown()
    health = coordinator.health_check()
    assert health.healthy is False


def test_health_check_lists_components(coordinator: FilesystemRuntimeCoordinator) -> None:
    health = coordinator.health_check()
    assert len(health.registered_components) >= 5


def test_health_check_uptime_positive(coordinator: FilesystemRuntimeCoordinator) -> None:
    health = coordinator.health_check()
    assert health.uptime_seconds >= 0.0


def test_health_check_frozen(coordinator: FilesystemRuntimeCoordinator) -> None:
    # pyrefly: ignore [missing-import]
    from pydantic import ValidationError
    health = coordinator.health_check()
    with pytest.raises((TypeError, ValidationError)):
        health.healthy = False


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def test_get_statistics_returns_instance(coordinator: FilesystemRuntimeCoordinator) -> None:
    stats = coordinator.get_statistics()
    assert isinstance(stats, FilesystemStatistics)


def test_statistics_start_at_zero(coordinator: FilesystemRuntimeCoordinator) -> None:
    stats = coordinator.get_statistics()
    assert stats.operations_started == 0
    assert stats.operations_completed == 0
    assert stats.transactions_started == 0


def test_statistics_after_recording(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.record_operation_start()
    coordinator.record_operation_complete(duration_ms=10.0)
    coordinator.record_transaction_started()
    stats = coordinator.get_statistics()
    assert stats.operations_started == 1
    assert stats.operations_completed == 1
    assert stats.transactions_started == 1


def test_statistics_peak_concurrent(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.record_operation_start()
    coordinator.record_operation_start()
    coordinator.record_operation_complete()
    stats = coordinator.get_statistics()
    assert stats.peak_concurrent_operations >= 2


def test_clear_resets_statistics(coordinator: FilesystemRuntimeCoordinator) -> None:
    coordinator.record_operation_start()
    coordinator.record_operation_complete()
    coordinator.clear()
    stats = coordinator.get_statistics()
    assert stats.operations_started == 0
    assert stats.operations_completed == 0


# ---------------------------------------------------------------------------
# Component List
# ---------------------------------------------------------------------------

def test_list_components_returns_list(coordinator: FilesystemRuntimeCoordinator) -> None:
    components = coordinator.list_components()
    assert isinstance(components, list)
    assert len(components) >= 5


def test_list_components_includes_provider(coordinator: FilesystemRuntimeCoordinator) -> None:
    components = coordinator.list_components()
    assert "FilesystemProvider" in components


# ---------------------------------------------------------------------------
# Singleton Accessors
# ---------------------------------------------------------------------------

def test_get_filesystem_runtime_returns_coordinator() -> None:
    runtime = get_filesystem_runtime()
    assert isinstance(runtime, FilesystemRuntimeCoordinator)


def test_get_filesystem_runtime_is_singleton() -> None:
    r1 = get_filesystem_runtime()
    r2 = get_filesystem_runtime()
    assert r1 is r2


def test_reset_filesystem_runtime_creates_new_instance() -> None:
    r1 = get_filesystem_runtime()
    reset_filesystem_runtime()
    r2 = get_filesystem_runtime()
    assert r1 is not r2


def test_runtime_status_ready_after_get() -> None:
    runtime = get_filesystem_runtime()
    assert runtime.status == FilesystemRuntimeStatus.READY


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_runtime_thread_safe_health_checks(coordinator: FilesystemRuntimeCoordinator) -> None:
    results = []

    def check() -> None:
        results.append(coordinator.health_check())

    threads = [threading.Thread(target=check) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(isinstance(r, FilesystemHealth) for r in results)
    assert len(results) == 20
