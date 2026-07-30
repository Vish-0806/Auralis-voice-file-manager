"""Unit tests for BrainController (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    BrainController, BrainRequest, BrainResponse,
    BrainRuntimeHealth, BrainRuntimeStatistics,
)


@pytest.fixture
def controller() -> BrainController:
    c = BrainController()
    c.initialize()
    return c


# ---------------------------------------------------------------------------
# Controller Entry Points
# ---------------------------------------------------------------------------

def test_controller_initialize(controller: BrainController) -> None:
    assert controller.initialize() is True


def test_controller_process_request_string(controller: BrainController) -> None:
    res = controller.process_request("search images")
    assert isinstance(res, BrainResponse)
    assert res.success is True


def test_controller_process_request_object(controller: BrainController) -> None:
    req = BrainRequest(request_id="r1", session_id="s1", raw_text="delete temp")
    res = controller.process_request(req)
    assert res.request_id == "r1"
    assert res.success is True


def test_controller_health_check(controller: BrainController) -> None:
    h = controller.health_check()
    assert isinstance(h, BrainRuntimeHealth)
    assert h.healthy is True


def test_controller_get_statistics(controller: BrainController) -> None:
    st = controller.get_statistics()
    assert isinstance(st, BrainRuntimeStatistics)


def test_controller_list_components(controller: BrainController) -> None:
    comps = controller.list_components()
    assert isinstance(comps, list)


def test_controller_restart(controller: BrainController) -> None:
    assert controller.restart() is True


def test_controller_shutdown(controller: BrainController) -> None:
    assert controller.shutdown() is True


def test_controller_clear(controller: BrainController) -> None:
    controller.process_request("test")
    controller.clear()
    assert controller.get_statistics().total_requests == 0


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_brain_controller_thread_safety(controller: BrainController) -> None:
    import threading
    results = []

    def worker(i: int) -> None:
        res = controller.process_request(f"cmd_{i}")
        results.append(res)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all(r.success for r in results)
