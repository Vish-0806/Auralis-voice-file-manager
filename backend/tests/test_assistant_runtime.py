"""Unit tests for AssistantRuntime (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    AssistantRuntime, BrainRequest, BrainResponse,
    BrainRuntimeHealth, BrainRuntimeStatistics,
)


@pytest.fixture
def runtime() -> AssistantRuntime:
    art = AssistantRuntime()
    art.initialize()
    return art


# ---------------------------------------------------------------------------
# Lifecycle & Request Processing
# ---------------------------------------------------------------------------

def test_assistant_runtime_initialize(runtime: AssistantRuntime) -> None:
    assert runtime.is_initialized is True


def test_assistant_runtime_process_string_request(runtime: AssistantRuntime) -> None:
    res = runtime.process_request("list downloads")
    assert isinstance(res, BrainResponse)
    assert res.success is True
    assert res.duration_ms >= 0.0


def test_assistant_runtime_process_object_request(runtime: AssistantRuntime) -> None:
    req = BrainRequest(request_id="req-obj", session_id="sess-obj", raw_text="open report")
    res = runtime.process_request(req)
    assert res.request_id == "req-obj"
    assert res.session_id == "sess-obj"
    assert res.success is True


def test_assistant_runtime_shutdown(runtime: AssistantRuntime) -> None:
    assert runtime.shutdown() is True
    assert runtime.is_initialized is False


def test_assistant_runtime_restart(runtime: AssistantRuntime) -> None:
    assert runtime.restart() is True
    assert runtime.is_initialized is True


def test_assistant_runtime_clear(runtime: AssistantRuntime) -> None:
    runtime.process_request("test")
    runtime.clear()
    stats = runtime.get_statistics()
    assert stats.total_requests == 0


def test_assistant_runtime_health_and_stats(runtime: AssistantRuntime) -> None:
    h = runtime.health_check()
    assert isinstance(h, BrainRuntimeHealth)
    assert h.healthy is True

    s = runtime.get_statistics()
    assert isinstance(s, BrainRuntimeStatistics)


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_assistant_runtime_thread_safety(runtime: AssistantRuntime) -> None:
    import threading
    responses = []

    def worker(i: int) -> None:
        res = runtime.process_request(f"command {i}")
        responses.append(res)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(responses) == 20
    assert all(r.success for r in responses)
