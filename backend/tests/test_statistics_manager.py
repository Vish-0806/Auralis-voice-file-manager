"""Unit tests for StatisticsManager (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    BrainRuntimeStatistics, DependencyRegistry,
    RuntimeComponent, StatisticsManager,
)


@pytest.fixture
def registry() -> DependencyRegistry:
    reg = DependencyRegistry()
    reg.resolve_all()
    return reg


@pytest.fixture
def stats_mgr(registry: DependencyRegistry) -> StatisticsManager:
    return StatisticsManager(registry=registry)


# ---------------------------------------------------------------------------
# Recording & Statistics Query
# ---------------------------------------------------------------------------

def test_initial_statistics_zero(stats_mgr: StatisticsManager) -> None:
    st = stats_mgr.get_statistics()
    assert isinstance(st, BrainRuntimeStatistics)
    assert st.total_requests == 0
    assert st.successful_requests == 0
    assert st.failed_requests == 0


def test_record_request_start_and_complete(stats_mgr: StatisticsManager) -> None:
    stats_mgr.record_request_start()
    stats_mgr.record_request_complete(duration_ms=15.0, success=True)

    st = stats_mgr.get_statistics()
    assert st.total_requests == 1
    assert st.successful_requests == 1
    assert st.failed_requests == 0
    assert st.average_pipeline_ms == 15.0


def test_record_failed_request(stats_mgr: StatisticsManager) -> None:
    stats_mgr.record_request_start()
    stats_mgr.record_request_complete(duration_ms=5.0, success=False)

    st = stats_mgr.get_statistics()
    assert st.total_requests == 1
    assert st.successful_requests == 0
    assert st.failed_requests == 1


def test_get_subsystem_statistics(stats_mgr: StatisticsManager) -> None:
    voice_stats = stats_mgr.get_subsystem_statistics(RuntimeComponent.VOICE)
    assert isinstance(voice_stats, dict)


def test_clear_statistics(stats_mgr: StatisticsManager) -> None:
    stats_mgr.record_request_start()
    stats_mgr.record_request_complete(duration_ms=10.0)
    stats_mgr.clear()

    st = stats_mgr.get_statistics()
    assert st.total_requests == 0
    assert st.average_pipeline_ms == 0.0


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_statistics_manager_thread_safety(stats_mgr: StatisticsManager) -> None:
    import threading

    def worker(i: int) -> None:
        stats_mgr.record_request_start()
        stats_mgr.record_request_complete(duration_ms=float(i), success=i % 2 == 0)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    st = stats_mgr.get_statistics()
    assert st.total_requests == 30
    assert st.successful_requests + st.failed_requests == 30
