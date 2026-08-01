"""Audit Logger implementation (Phase 11.8).

Provides thread-safe recording and filtering of security decision audit events,
decision metrics, and severity classification.
"""

from datetime import datetime, timezone
import threading
import uuid
from typing import List, Optional

from brain.os.security.interfaces import IAuditLogger
from brain.os.security.security_models import (
    AuditEvent,
    AuditSeverity,
    OperationCategory,
    RiskLevel,
    SecurityDecision,
    SecurityDecisionType,
    SecurityRequest,
)


class AuditLogger(IAuditLogger):
    """Thread-safe security decision audit logger."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: List[AuditEvent] = []

    def _determine_severity(self, decision: SecurityDecision) -> AuditSeverity:
        """Map decision decision_type and risk_level to AuditSeverity."""
        if decision.decision_type == SecurityDecisionType.DENY:
            return AuditSeverity.ERROR
        elif decision.risk_assessment.risk_level == RiskLevel.CRITICAL:
            return AuditSeverity.CRITICAL
        elif decision.risk_assessment.risk_level == RiskLevel.HIGH or decision.decision_type == SecurityDecisionType.REQUIRE_CONFIRMATION:
            return AuditSeverity.WARNING
        return AuditSeverity.INFO

    def log_decision(
        self, request: SecurityRequest, decision: SecurityDecision
    ) -> AuditEvent:
        """Record a security decision event in the audit trail."""
        with self._lock:
            event_id = f"audit_{uuid.uuid4().hex[:8]}"
            sev = self._determine_severity(decision)

            event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.now(timezone.utc),
                request_id=request.request_id,
                category=request.category,
                operation=request.operation,
                target_resource=request.target_resource,
                decision_type=decision.decision_type,
                risk_level=decision.risk_assessment.risk_level,
                severity=sev,
                reason=decision.reason,
            )

            self._events.append(event)
            return event

    def get_audit_history(
        self, category: Optional[OperationCategory] = None
    ) -> List[AuditEvent]:
        """Retrieve recorded audit trail events."""
        with self._lock:
            if not category:
                return list(self._events)
            return [e for e in self._events if e.category == category]

    def clear_audit_history(self) -> None:
        """Clear audit history log."""
        with self._lock:
            self._events.clear()
