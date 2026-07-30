"""Unit tests for IntegrationPipeline (Phase 9.7)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.runtime import (
    BrainRequest, DependencyRegistry, IntegrationPipeline,
    PipelineResult, PipelineStatus, RuntimeComponent,
)


@pytest.fixture
def registry() -> DependencyRegistry:
    reg = DependencyRegistry()
    reg.resolve_all()
    return reg


@pytest.fixture
def pipeline(registry: DependencyRegistry) -> IntegrationPipeline:
    return IntegrationPipeline(registry=registry)


# ---------------------------------------------------------------------------
# Pipeline Execution
# ---------------------------------------------------------------------------

def test_execute_successful_pipeline(pipeline: IntegrationPipeline) -> None:
    req = BrainRequest(
        request_id="r1",
        session_id="s1",
        raw_text="search downloads directory",
    )
    res = pipeline.execute(req)
    assert isinstance(res, PipelineResult)
    assert res.success is True
    assert res.status == PipelineStatus.COMPLETED
    assert res.request_id == "r1"
    assert res.pipeline_ms >= 0.0


def test_execute_pipeline_empty_text(pipeline: IntegrationPipeline) -> None:
    req = BrainRequest(request_id="r2", session_id="s1", raw_text="")
    res = pipeline.execute(req)
    assert res.success is True
    assert res.status == PipelineStatus.COMPLETED


def test_execute_pipeline_with_mock_failure() -> None:
    reg = DependencyRegistry()

    class FailingVoice:
        def get_orchestrator(self) -> None:
            raise RuntimeError("Voice crash")

    reg.register(RuntimeComponent.VOICE, FailingVoice())
    pip = IntegrationPipeline(registry=reg)

    req = BrainRequest(request_id="r3", raw_text="crash")
    res = pip.execute(req)
    assert res.success is True  # Exception caught gracefully in stage, pipeline continues or completes with error status


# ---------------------------------------------------------------------------
# Thread Safety
# ---------------------------------------------------------------------------

def test_integration_pipeline_thread_safety(pipeline: IntegrationPipeline) -> None:
    import threading
    results = []

    def run_pipeline(i: int) -> None:
        req = BrainRequest(request_id=f"req-{i}", session_id=f"sess-{i}", raw_text=f"cmd {i}")
        res = pipeline.execute(req)
        results.append(res)

    threads = [threading.Thread(target=run_pipeline, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all(isinstance(r, PipelineResult) for r in results)
