"""Risk Analyzer implementation (Phase 11.8).

Performs risk scoring and factor classification (LOW, MEDIUM, HIGH, CRITICAL) based on
operation category, action severity, and target resource sensitivity.
"""

from typing import List

from brain.os.security.interfaces import IRiskAnalyzer
from brain.os.security.security_models import (
    OperationCategory,
    PermissionLevel,
    RiskAssessment,
    RiskLevel,
    SecurityRequest,
)


class RiskAnalyzer(IRiskAnalyzer):
    """Provides request risk analysis and factor classification."""

    def analyze_risk(self, request: SecurityRequest) -> RiskAssessment:
        """Perform risk assessment and factor classification for a request."""
        op_lower = request.operation.lower()
        target_lower = request.target_resource.lower()
        cat = request.category

        factors: List[str] = []
        is_dangerous = False
        is_destructive = False
        risk_level = RiskLevel.LOW
        score = 0.1

        # 1. Check critical destructive operations
        if "format" in op_lower or "partition" in op_lower or "wipe" in op_lower:
            risk_level = RiskLevel.CRITICAL
            score = 1.0
            is_dangerous = True
            is_destructive = True
            factors.append("Disk format/wipe operation")

        elif cat == OperationCategory.PROCESS and ("explorer" in target_lower or "systemd" in target_lower or "init" in target_lower):
            risk_level = RiskLevel.CRITICAL
            score = 0.95
            is_dangerous = True
            is_destructive = True
            factors.append("Critical shell/system process termination")

        # 2. Check high risk system operations
        elif "system32" in target_lower or "/etc" in target_lower or "registry" in op_lower:
            risk_level = RiskLevel.HIGH
            score = 0.8
            is_dangerous = True
            if "delete" in op_lower or "remove" in op_lower:
                is_destructive = True
            factors.append("System file or registry modification")

        elif request.requested_permission == PermissionLevel.ADMIN:
            risk_level = RiskLevel.HIGH
            score = 0.75
            is_dangerous = True
            factors.append("Administrator privilege request")

        # 3. Check medium risk operations
        elif cat in (OperationCategory.PROCESS, OperationCategory.DEVICE) and ("terminate" in op_lower or "disable" in op_lower):
            risk_level = RiskLevel.MEDIUM
            score = 0.5
            is_dangerous = True
            factors.append("Process or device state modification")

        elif "delete" in op_lower or "remove" in op_lower:
            risk_level = RiskLevel.MEDIUM
            score = 0.4
            is_destructive = True
            factors.append("Resource deletion")

        # 4. Low risk operations
        else:
            factors.append("Standard user operation")

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=score,
            factors=factors,
            is_dangerous=is_dangerous,
            is_destructive=is_destructive,
        )
