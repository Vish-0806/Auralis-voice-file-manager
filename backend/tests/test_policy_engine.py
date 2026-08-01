"""Unit tests for PolicyEngine (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    OperationCategory,
    PermissionLevel,
    PermissionResult,
    PolicyEngine,
    SecurityDecisionType,
    SecurityRequest,
)


def test_policy_engine_allow_and_deny() -> None:
    pe = PolicyEngine()
    req = SecurityRequest(
        request_id="p1",
        category=OperationCategory.FILESYSTEM,
        operation="write_file",
        requested_permission=PermissionLevel.WRITE,
    )

    perm_ok = PermissionResult(granted=True, permission=PermissionLevel.WRITE)
    assert pe.evaluate_policy(req, perm_ok) == SecurityDecisionType.ALLOW

    pe.set_policy(OperationCategory.FILESYSTEM, SecurityDecisionType.DENY)
    assert pe.evaluate_policy(req, perm_ok) == SecurityDecisionType.DENY


def test_policy_engine_read_only() -> None:
    pe = PolicyEngine()
    pe.set_policy(OperationCategory.FILESYSTEM, SecurityDecisionType.READ_ONLY)

    req_read = SecurityRequest(category=OperationCategory.FILESYSTEM, requested_permission=PermissionLevel.READ)
    req_write = SecurityRequest(category=OperationCategory.FILESYSTEM, requested_permission=PermissionLevel.WRITE)

    perm_ok = PermissionResult(granted=True, permission=PermissionLevel.READ)
    assert pe.evaluate_policy(req_read, perm_ok) == SecurityDecisionType.ALLOW
    assert pe.evaluate_policy(req_write, perm_ok) == SecurityDecisionType.DENY
