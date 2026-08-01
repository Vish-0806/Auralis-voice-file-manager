"""Unit tests for SecurityRuntime and singleton accessors (Phase 11.8)."""

import threading
# pyrefly: ignore [missing-import]
import pytest

from brain.os.security import (
    OperationCategory,
    SecurityDecision,
    SecurityDecisionType,
    SecurityProvider,
    SecurityRequest,
    SecurityRuntime,
    SecurityRuntimeStatus,
    get_security_runtime,
    reset_security_runtime,
)


def test_security_runtime_lifecycle() -> None:
    rt = SecurityRuntime()
    assert rt.get_health().state == "Initializing"

    rt.initialize()
    assert rt.get_health().state == "Running"

    provider = rt.get_provider()
    assert isinstance(provider, SecurityProvider)

    req = SecurityRequest(category=OperationCategory.FILESYSTEM, operation="read")
    dec = rt.evaluate_request(req)
    assert isinstance(dec, SecurityDecision)

    rt.shutdown()
    assert rt.get_health().state == "Stopped"


def test_security_runtime_singleton() -> None:
    reset_security_runtime()
    rt1 = get_security_runtime()
    rt2 = get_security_runtime()

    assert rt1 is rt2
    assert rt1.get_health().state == "Running"

    reset_security_runtime()
    rt3 = get_security_runtime()
    assert rt3 is not rt1


def test_security_runtime_thread_safety() -> None:
    reset_security_runtime()
    rt = get_security_runtime()

    def worker() -> None:
        for _ in range(50):
            req = SecurityRequest(category=OperationCategory.FILESYSTEM, operation="read")
            rt.evaluate_request(req)
            rt.get_statistics()
            rt.get_health()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert rt.get_health().state == "Running"
