"""Unit tests for Phase 11.9 Integration Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.integration import (
    CapabilityDescriptor,
    DispatchStrategy,
    ExecutionState,
    ExecutionStatistics,
    ExecutionSummary,
    IntegrationHealth,
    IntegrationStatus,
    OperationContext,
    OperationRequest,
    OperationResponse,
    OperationResult,
    OperationTarget,
    OperationType,
)


def test_integration_enums() -> None:
    assert OperationTarget.FILESYSTEM.value == "filesystem"
    assert OperationType.READ.value == "read"
    assert ExecutionState.COMPLETED.value == "completed"
    assert DispatchStrategy.SECURE.value == "secure"


def test_operation_context_defaults_and_immutability() -> None:
    ctx = OperationContext(user_id="user_1", is_admin=True)
    assert ctx.user_id == "user_1"
    assert ctx.is_admin is True

    with pytest.raises((TypeError, ValidationError)):
        ctx.user_id = "user_2"  # type: ignore


def test_operation_request_defaults_and_immutability() -> None:
    req = OperationRequest(
        request_id="req_100",
        target=OperationTarget.FILESYSTEM,
        capability="filesystem.open",
        action="read",
    )
    assert req.request_id == "req_100"
    assert req.target == OperationTarget.FILESYSTEM

    with pytest.raises((TypeError, ValidationError)):
        req.capability = "filesystem.write"  # type: ignore


def test_operation_response_defaults_and_immutability() -> None:
    res = OperationResponse(request_id="req_100", success=True)
    assert res.request_id == "req_100"
    assert res.success is True

    with pytest.raises((TypeError, ValidationError)):
        res.success = False  # type: ignore
