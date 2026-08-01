"""Unit tests for OperatingSystemRuntime and runtime singleton (Phase 11.1)."""

import threading

from brain.os import (
    OperatingSystemProvider,
    OperatingSystemRuntime,
    OSRuntimeStatus,
    RuntimeState,
    RuntimeStatistics,
    get_os_runtime,
    reset_os_runtime,
)


def test_os_runtime_lifecycle() -> None:
    runtime = OperatingSystemRuntime()
    assert runtime.get_health().state == RuntimeState.INITIALIZING

    runtime.initialize()
    assert runtime.get_health().state == RuntimeState.RUNNING

    provider = runtime.get_provider()
    assert isinstance(provider, OperatingSystemProvider)

    runtime.shutdown()
    assert runtime.get_health().state == RuntimeState.STOPPED


def test_os_runtime_statistics() -> None:
    runtime = OperatingSystemRuntime()
    runtime.initialize()

    runtime.record_request(request_type="platform")
    runtime.record_request(request_type="environment")
    runtime.record_request(request_type="path")
    runtime.record_request(request_type="path", is_error=True)

    stats = runtime.get_statistics()
    assert isinstance(stats, RuntimeStatistics)
    assert stats.total_requests == 4
    assert stats.platform_checks == 1
    assert stats.environment_snapshots == 1
    assert stats.path_resolutions == 2
    assert stats.errors_encountered == 1


def test_os_runtime_provider_registration() -> None:
    runtime = OperatingSystemRuntime()
    custom_provider = OperatingSystemProvider()

    runtime.register_provider(custom_provider)
    assert runtime.get_provider() is custom_provider


def test_os_runtime_singleton_access() -> None:
    reset_os_runtime()
    rt1 = get_os_runtime()
    rt2 = get_os_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == RuntimeState.RUNNING

    reset_os_runtime()
    rt3 = get_os_runtime()
    assert rt3 is not rt1


def test_os_runtime_thread_safety() -> None:
    reset_os_runtime()
    runtime = get_os_runtime()

    def worker() -> None:
        for _ in range(50):
            runtime.record_request(request_type="path")
            runtime.get_statistics()
            runtime.get_health()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = runtime.get_statistics()
    assert stats.total_requests == 500
