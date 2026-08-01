"""Unit tests for ExecutionPipeline (Phase 11.9)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.integration import (
    ExecutionPipeline,
    ExecutionState,
    OperationRequest,
    OperationResponse,
    OperationTarget,
)


def test_execution_pipeline_success_flow() -> None:
    pipeline = ExecutionPipeline()
    req = OperationRequest(
        request_id="p1",
        target=OperationTarget.FILESYSTEM,
        capability="filesystem.open",
        target_resource="/data/test.txt",
    )

    resp = pipeline.execute_pipeline(req)
    assert isinstance(resp, OperationResponse)
    assert resp.success is True
    assert resp.summary.state == ExecutionState.COMPLETED
    assert ExecutionState.EVALUATING_SECURITY.value in resp.summary.stages
    assert ExecutionState.DISPATCHING.value in resp.summary.stages


def test_execution_pipeline_invalid_capability() -> None:
    pipeline = ExecutionPipeline()
    req = OperationRequest(
        request_id="p2",
        target=OperationTarget.SYSTEM,
        capability="invalid.fake.capability",
    )

    resp = pipeline.execute_pipeline(req)
    assert resp.success is False
    assert resp.summary.state == ExecutionState.FAILED
