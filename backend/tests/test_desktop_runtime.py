"""Unit tests for DesktopRuntime and singleton accessors (Phase 11.5)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.os.desktop import (
    DesktopProvider,
    DesktopRuntime,
    DesktopRuntimeStatus,
    get_desktop_runtime,
    reset_desktop_runtime,
)


def test_desktop_runtime_lifecycle() -> None:
    rt = DesktopRuntime()
    assert rt.get_health().state == "Initializing"

    rt.initialize()
    assert rt.get_health().state == "Running"

    provider = rt.get_provider()
    assert isinstance(provider, DesktopProvider)

    rt.shutdown()
    assert rt.get_health().state == "Stopped"


def test_desktop_runtime_singleton() -> None:
    reset_desktop_runtime()
    rt1 = get_desktop_runtime()
    rt2 = get_desktop_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == "Running"

    reset_desktop_runtime()
    rt3 = get_desktop_runtime()
    assert rt3 is not rt1


def test_desktop_runtime_thread_safety() -> None:
    reset_desktop_runtime()
    rt = get_desktop_runtime()

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
