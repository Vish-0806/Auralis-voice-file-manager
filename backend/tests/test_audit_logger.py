"""Unit tests for AuditLogger (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    AuditEvent,
    AuditLogger,
    OperationCategory,
    SecurityDecision,
    SecurityDecisionType,
    SecurityRequest,
)


def test_audit_logger_log_and_filter() -> None:
    al = AuditLogger()
    req = SecurityRequest(request_id="a1", category=OperationCategory.FILESYSTEM, operation="write")
    dec = SecurityDecision(request_id="a1", decision_type=SecurityDecisionType.ALLOW)

    event = al.log_decision(req, dec)
    assert isinstance(event, AuditEvent)
    assert event.request_id == "a1"

    hist = al.get_audit_history(OperationCategory.FILESYSTEM)
    assert len(hist) == 1

    hist_proc = al.get_audit_history(OperationCategory.PROCESS)
    assert len(hist_proc) == 0

    al.clear_audit_history()
    assert len(al.get_audit_history()) == 0
