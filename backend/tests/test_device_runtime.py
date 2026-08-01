"""Unit tests for DeviceRuntime and singleton accessors (Phase 11.7)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.os.device import (
    DeviceProvider,
    DeviceRuntime,
    DeviceRuntimeStatus,
    get_device_runtime,
    reset_device_runtime,
)


def test_device_runtime_lifecycle() -> None:
    rt = DeviceRuntime()
    assert rt.get_health().state == "Initializing"

    rt.initialize()
    assert rt.get_health().state == "Running"

    provider = rt.get_provider()
    assert isinstance(provider, DeviceProvider)

    rt.shutdown()
    assert rt.get_health().state == "Stopped"


def test_device_runtime_singleton() -> None:
    reset_device_runtime()
    rt1 = get_device_runtime()
    rt2 = get_device_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == "Running"

    reset_device_runtime()
    rt3 = get_device_runtime()
    assert rt3 is not rt1


def test_device_runtime_thread_safety() -> None:
    reset_device_runtime()
    rt = get_device_runtime()

    def worker() -> None:
        for _ in range(50):
            rt.get_statistics()
            rt.get_health()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert rt.get_health().state == "Running"
