"""Unit tests for FilesystemRuntime and singleton accessors (Phase 11.2)."""

import threading
import pytest

from brain.os.filesystem import (
    FilesystemCapabilities,
    FilesystemHealth,
    FilesystemProvider,
    FilesystemRuntime,
    FilesystemRuntimeStatus,
    FilesystemStatistics,
    get_filesystem_runtime,
    reset_filesystem_runtime,
)


def test_filesystem_runtime_lifecycle() -> None:
    rt = FilesystemRuntime()
    assert rt.get_health().state == "Initializing"

    rt.initialize()
    assert rt.get_health().state == "Running"

    provider = rt.get_provider()
    assert isinstance(provider, FilesystemProvider)

    rt.shutdown()
    assert rt.get_health().state == "Stopped"


def test_filesystem_runtime_statistics() -> None:
    rt = FilesystemRuntime()
    rt.initialize()

    rt.record_operation("read_text", bytes_count=100)
    rt.record_operation("write_text", bytes_count=200)
    rt.record_operation("delete_file")
    rt.record_operation("search")
    rt.record_operation("read_text", is_error=True)

    stats = rt.get_statistics()
    assert isinstance(stats, FilesystemStatistics)
    assert stats.total_operations == 5
    assert stats.reads_count == 2
    assert stats.writes_count == 1
    assert stats.deletes_count == 1
    assert stats.searches_count == 1
    assert stats.bytes_read == 100
    assert stats.bytes_written == 200
    assert stats.errors_count == 1


def test_filesystem_provider_health_and_capabilities() -> None:
    provider = FilesystemProvider()

    health = provider.get_health()
    assert isinstance(health, FilesystemHealth)
    assert health.healthy is True
    assert health.status == "READY"

    caps = provider.get_capabilities()
    assert isinstance(caps, FilesystemCapabilities)
    assert caps.supports_transactions is True
    assert caps.supports_atomic_writes is True

    diag = provider.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["provider_type"] == "FilesystemProvider"


def test_filesystem_runtime_singleton() -> None:
    reset_filesystem_runtime()
    rt1 = get_filesystem_runtime()
    rt2 = get_filesystem_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == "Running"

    reset_filesystem_runtime()
    rt3 = get_filesystem_runtime()
    assert rt3 is not rt1


def test_filesystem_runtime_thread_safety() -> None:
    reset_filesystem_runtime()
    rt = get_filesystem_runtime()

    def worker() -> None:
        for _ in range(50):
            rt.record_operation("read_text", bytes_count=10)
            rt.get_statistics()
            rt.get_health()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = rt.get_statistics()
    assert stats.total_operations == 500
