"""Unit tests for Phase 11.8 Security Runtime domain models."""

from datetime import datetime
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.os.security import (
    AuditEvent,
    AuditSeverity,
    ConfirmationPolicy,
    ConfirmationRequest,
    OperationCategory,
    PermissionLevel,
    PermissionResult,
    RiskAssessment,
    RiskLevel,
    SecurityCapabilities,
    SecurityContext,
    SecurityDecision,
    SecurityDecisionType,
    SecurityHealth,
    SecurityRequest,
    SecurityRuntimeStatus,
    SecurityStatistics,
)


def test_security_enums() -> None:
    assert PermissionLevel.READ.value == "read"
    assert SecurityDecisionType.ALLOW.value == "allow"
    assert RiskLevel.HIGH.value == "high"
    assert ConfirmationPolicy.DANGEROUS_ONLY.value == "dangerous_only"
    assert AuditSeverity.CRITICAL.value == "critical"
    assert OperationCategory.FILESYSTEM.value == "filesystem"


def test_security_context_defaults_and_immutability() -> None:
    ctx = SecurityContext(user_id="alice", is_admin=True)
    assert ctx.user_id == "alice"
    assert ctx.is_admin is True

    with pytest.raises((TypeError, ValidationError)):
        ctx.user_id = "bob"  # type: ignore


def test_security_request_defaults_and_immutability() -> None:
    req = SecurityRequest(request_id="req_1", category=OperationCategory.FILESYSTEM, operation="read_file")
    assert req.request_id == "req_1"
    assert req.category == OperationCategory.FILESYSTEM

    with pytest.raises((TypeError, ValidationError)):
        req.operation = "delete_file"  # type: ignore


def test_security_decision_defaults_and_immutability() -> None:
    dec = SecurityDecision(request_id="req_100", decision_type=SecurityDecisionType.ALLOW)
    assert dec.request_id == "req_100"
    assert dec.decision_type == SecurityDecisionType.ALLOW

    with pytest.raises((TypeError, ValidationError)):
        dec.decision_type = SecurityDecisionType.DENY  # type: ignore
