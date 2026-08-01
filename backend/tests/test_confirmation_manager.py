"""Unit tests for ConfirmationManager (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    ConfirmationManager,
    ConfirmationPolicy,
    ConfirmationRequest,
    PermissionResult,
    RiskAssessment,
    RiskLevel,
    SecurityRequest,
)


def test_confirmation_manager_policies() -> None:
    cm = ConfirmationManager(policy=ConfirmationPolicy.DANGEROUS_ONLY)
    req = SecurityRequest(request_id="c1", operation="delete", target_resource="important.dat")
    perm = PermissionResult(granted=True)

    risk_low = RiskAssessment(risk_level=RiskLevel.LOW, is_dangerous=False)
    assert cm.evaluate_confirmation(req, risk_low, perm) is None

    risk_high = RiskAssessment(risk_level=RiskLevel.HIGH, is_dangerous=True)
    conf = cm.evaluate_confirmation(req, risk_high, perm)
    assert isinstance(conf, ConfirmationRequest)
    assert conf.request_id == "c1"
