"""API Violation Tracker Implementation (Phase 15.8).

Thread-safe violation tracker recording client rate limit and policy violations,
managing cooldown periods, and purging expired records without networking dependencies.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple

from backend.application.api.protection.interfaces import IViolationTracker
from backend.application.api.protection.models import ViolationRecord

logger = logging.getLogger(__name__)


class ViolationTracker(IViolationTracker):
    """Thread-safe violation tracker recording security and rate limit violations."""

    def __init__(self) -> None:
        """Initialize ViolationTracker using Constructor Dependency Injection."""
        self._lock = RLock()
        self._violations: List[ViolationRecord] = []

        self._total_recorded_violations = 0
        self._total_purged_violations = 0

    def record_violation(self, violation: ViolationRecord) -> ViolationRecord:
        """Record a new violation event.

        Args:
            violation: Immutable ViolationRecord instance.

        Returns:
            ViolationRecord: Recorded violation model.
        """
        with self._lock:
            self._violations.append(violation)
            self._total_recorded_violations += 1
            logger.warning(
                "Recorded violation ID '%s' for client '%s' (rule: %s).",
                violation.violation_id,
                violation.client_id,
                violation.rule_id,
            )
            return violation

    def list_violations(
        self, client_id: Optional[str] = None
    ) -> Tuple[ViolationRecord, ...]:
        """List violation records, optionally filtered by client ID.

        Args:
            client_id: Optional client ID filter.

        Returns:
            Tuple[ViolationRecord, ...]: Immutable tuple of matching violation records.
        """
        with self._lock:
            if client_id is None:
                return tuple(self._violations)
            return tuple(v for v in self._violations if v.client_id == client_id)

    def is_client_in_cooldown(self, client_id: str) -> bool:
        """Check if a client is currently in an active cooldown window.

        Args:
            client_id: Unique client identifier.

        Returns:
            bool: True if client has an active unexpired cooldown, else False.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            for v in self._violations:
                if v.client_id == client_id and v.cooldown_until is not None:
                    if now < v.cooldown_until:
                        return True
            return False

    def count_violations(self) -> int:
        """Get total count of recorded violation records.

        Returns:
            int: Violation count.
        """
        with self._lock:
            return len(self._violations)

    def clear_expired_violations(self) -> int:
        """Purge expired violation records past their cooldown period.

        Returns:
            int: Count of purged records.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            active: List[ViolationRecord] = []
            purged_count = 0

            for v in self._violations:
                if v.cooldown_until is not None and now >= v.cooldown_until:
                    purged_count += 1
                else:
                    active.append(v)

            self._violations = active
            self._total_purged_violations += purged_count
            logger.info("Purged %d expired violation records.", purged_count)
            return purged_count

    def clear(self) -> None:
        """Clear all violation records from the tracker."""
        with self._lock:
            self._violations.clear()
            logger.info("ViolationTracker cleared.")

    def get_tracker_telemetry(self) -> Dict[str, int]:
        """Get internal violation tracker telemetry counters under lock."""
        with self._lock:
            return {
                "total_recorded_violations": self._total_recorded_violations,
                "total_purged_violations": self._total_purged_violations,
                "current_violations_count": len(self._violations),
            }
