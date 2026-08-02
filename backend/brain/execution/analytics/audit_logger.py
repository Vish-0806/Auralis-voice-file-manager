"""Audit Logger for the Auralis Execution Analytics & Observability Runtime (Phase 12.7).

Records immutable audit trail logs for execution events across workflow, task, automation, and security decisions.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional

from brain.execution.analytics.interfaces import IAuditLogger
from brain.execution.analytics.analytics_models import (
    AuditSeverity,
    ExecutionAuditRecord,
    ExecutionOutcome,
)


class AuditLogger(IAuditLogger):
    """Thread-safe audit logger recording immutable audit records."""

    def __init__(self) -> None:
        """Initializes AuditLogger."""
        self._lock = threading.RLock()
        self._records: List[ExecutionAuditRecord] = []

    def log_audit(
        self,
        event_type: str,
        subsystem: str,
        action: str,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        outcome: ExecutionOutcome = ExecutionOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> ExecutionAuditRecord:
        """Log an immutable audit record.

        Args:
            event_type: Category of event (e.g. WORKFLOW_EXECUTION, TASK_EXECUTION, SECURITY_DECISION).
            subsystem: Target subsystem name string.
            action: Action executed.
            severity: AuditSeverity enum (LOW, MEDIUM, HIGH, CRITICAL).
            outcome: ExecutionOutcome enum (SUCCESS, FAILURE, ABORTED, CANCELLED, TIMEOUT).
            details: Optional dictionary with additional event context details.

        Returns:
            ExecutionAuditRecord model.
        """
        with self._lock:
            record = ExecutionAuditRecord(
                event_type=event_type,
                subsystem=subsystem,
                action=action,
                severity=severity,
                outcome=outcome,
                details=dict(details or {}),
                timestamp=datetime.now(timezone.utc),
            )
            self._records.append(record)
            return record

    def get_audit_records(self, subsystem_filter: Optional[str] = None) -> List[ExecutionAuditRecord]:
        """Fetch recorded audit logs matching optional subsystem filter.

        Args:
            subsystem_filter: Optional subsystem name string.

        Returns:
            List of ExecutionAuditRecord models.
        """
        with self._lock:
            if not subsystem_filter:
                return list(self._records)
            sub_lower = subsystem_filter.lower()
            return [r for r in self._records if sub_lower in r.subsystem.lower()]

    def count_records(self) -> int:
        """Return total count of recorded audit records."""
        with self._lock:
            return len(self._records)

    def clear(self) -> None:
        """Clear recorded audit logs."""
        with self._lock:
            self._records.clear()
