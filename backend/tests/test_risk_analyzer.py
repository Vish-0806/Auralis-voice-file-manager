"""Unit tests for RiskAnalyzer (Phase 11.8)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.security import (
    OperationCategory,
    RiskAnalyzer,
    RiskAssessment,
    RiskLevel,
    SecurityRequest,
)


def test_risk_analyzer_classifications() -> None:
    ra = RiskAnalyzer()

    req_low = SecurityRequest(
        category=OperationCategory.APPLICATION,
        operation="launch_application",
        target_resource="calc.exe",
    )
    risk_low = ra.analyze_risk(req_low)
    assert isinstance(risk_low, RiskAssessment)
    assert risk_low.risk_level == RiskLevel.LOW
    assert risk_low.is_dangerous is False

    req_crit = SecurityRequest(
        category=OperationCategory.SYSTEM,
        operation="format_drive",
        target_resource="C:\\",
    )
    risk_crit = ra.analyze_risk(req_crit)
    assert risk_crit.risk_level == RiskLevel.CRITICAL
    assert risk_crit.is_destructive is True
