"""Unit tests for WindowRuntime and singleton accessors (Phase 11.6)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.os.window import (
    WindowProvider,
    WindowRuntime,
    WindowRuntimeStatus,
    get_window_runtime,
    reset_window_runtime,
)


def test_window_runtime_lifecycle() -> None:
    rt = WindowRuntime()
    assert rt.get_health().state == "Initializing"

    rt.initialize()
    assert rt.get_health().state == "Running"

    provider = rt.get_provider()
    assert isinstance(provider, WindowProvider)

    rt.shutdown()
    assert rt.get_health().state == "Stopped"


def test_window_runtime_singleton() -> None:
    reset_window_runtime()
    rt1 = get_window_runtime()
    rt2 = get_window_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == "Running"

    reset_window_runtime()
    rt3 = get_window_runtime()
    assert rt3 is not rt1


def test_window_runtime_thread_safety() -> None:
    reset_window_runtime()
    rt = get_window_runtime()

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
