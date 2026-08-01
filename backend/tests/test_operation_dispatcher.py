"""Unit tests for OperationDispatcher (Phase 11.9)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.integration import (
    CapabilityDescriptor,
    OperationDispatcher,
    OperationRequest,
    OperationResult,
    OperationTarget,
)


def test_operation_dispatcher_dispatch() -> None:
    dispatcher = OperationDispatcher()
    req = OperationRequest(
        request_id="d1",
        target=OperationTarget.FILESYSTEM,
        capability="filesystem.open",
        target_resource="/path/file.txt",
    )
    desc = CapabilityDescriptor(capability_name="filesystem.open", target=OperationTarget.FILESYSTEM)

    res = dispatcher.dispatch(req, desc)
    assert isinstance(res, OperationResult)
    assert res.success is True
    assert "dispatched_filesystem" in res.data.get("status", "")
