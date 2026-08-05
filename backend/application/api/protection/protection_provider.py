"""API Protection Provider Implementation (Phase 15.8).

Thread-safe protection provider aggregating RateLimiter, PolicyEngine,
and ViolationTracker with full lifecycle management, health monitoring,
statistics tracking, and diagnostic telemetry.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
import threading
from typing import Optional, Tuple

from backend.application.api.protection.interfaces import (
    IPolicyEngine,
    IProtectionProvider,
    IRateLimiter,
    IViolationTracker,
)
from backend.application.api.protection.models import (
    ProtectionCapabilities,
    ProtectionDiagnostics,
    ProtectionHealth,
    ProtectionRuntimeState,
    ProtectionStatistics,
)
from backend.application.api.protection.policy_engine import PolicyEngine
from backend.application.api.protection.rate_limiter import RateLimiter
from backend.application.api.protection.violation_tracker import ViolationTracker

logger = logging.getLogger(__name__)


class ProtectionProvider(IProtectionProvider):
    """Production thread-safe protection provider aggregating protection components."""

    def __init__(
        self,
        rate_limiter: Optional[IRateLimiter] = None,
        policy_engine: Optional[IPolicyEngine] = None,
        violation_tracker: Optional[IViolationTracker] = None,
        capabilities: Optional[ProtectionCapabilities] = None,
    ) -> None:
        """Initialize ProtectionProvider using Constructor Dependency Injection.

        Args:
            rate_limiter: Optional IRateLimiter implementation instance.
            policy_engine: Optional IPolicyEngine implementation instance.
            violation_tracker: Optional IViolationTracker implementation instance.
            capabilities: Optional ProtectionCapabilities instance.
        """
        self._lock = RLock()
        self._rate_limiter = rate_limiter or RateLimiter()
        self._policy_engine = policy_engine or PolicyEngine(
            rate_limiter=self._rate_limiter
        )
        self._violation_tracker = violation_tracker or ViolationTracker()
        self._capabilities = capabilities or ProtectionCapabilities()

        self._status = ProtectionRuntimeState.UNINITIALIZED
        self._total_initializations = 0
        self._total_restarts = 0
        self._total_shutdowns = 0

    def initialize(self) -> ProtectionHealth:
        """Initialize the protection provider and transition state to READY.

        Returns:
            ProtectionHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status in (
                ProtectionRuntimeState.INITIALIZING,
                ProtectionRuntimeState.READY,
            ):
                return self.health()

            self._status = ProtectionRuntimeState.INITIALIZING
            logger.info("ProtectionProvider transitioning to INITIALIZING state.")

            self._status = ProtectionRuntimeState.READY
            self._total_initializations += 1
            logger.info("ProtectionProvider successfully initialized and READY.")
            return self.health()

    def shutdown(self) -> ProtectionHealth:
        """Shutdown the protection provider safely and transition state to STOPPED.

        Returns:
            ProtectionHealth: Updated health snapshot.
        """
        with self._lock:
            if self._status == ProtectionRuntimeState.STOPPED:
                return self.health()

            self._status = ProtectionRuntimeState.STOPPING
            logger.info("ProtectionProvider transitioning to STOPPING state.")

            self._status = ProtectionRuntimeState.STOPPED
            self._total_shutdowns += 1
            logger.info("ProtectionProvider successfully stopped.")
            return self.health()

    def restart(self) -> ProtectionHealth:
        """Restart the protection provider by shutting down if active, then initializing.

        Returns:
            ProtectionHealth: Updated health snapshot.
        """
        with self._lock:
            logger.info("ProtectionProvider restarting...")
            if self._status != ProtectionRuntimeState.STOPPED:
                self.shutdown()

            health = self.initialize()
            self._total_restarts += 1
            return health

    def health(self) -> ProtectionHealth:
        """Get health status evaluation snapshot.

        Returns:
            ProtectionHealth: Immutable health snapshot.
        """
        with self._lock:
            is_healthy = self._status in (
                ProtectionRuntimeState.READY,
                ProtectionRuntimeState.UNINITIALIZED,
            )
            issues: Tuple[str, ...] = ()
            if not is_healthy:
                issues = (f"Protection provider is in state: {self._status.value}",)

            return ProtectionHealth(
                is_healthy=is_healthy,
                state=self._status,
                details={
                    "status": self._status.value,
                    "rules_count": self._rate_limiter.count_rules(),
                    "policies_count": self._policy_engine.count_policies(),
                    "violations_count": self._violation_tracker.count_violations(),
                },
                issues=issues,
                checked_at=datetime.now(timezone.utc),
            )

    def statistics(self) -> ProtectionStatistics:
        """Get aggregate metrics and statistics.

        Returns:
            ProtectionStatistics: Immutable statistics snapshot.
        """
        with self._lock:
            total_rules = self._rate_limiter.count_rules()
            total_policies = self._policy_engine.count_policies()
            total_violations = self._violation_tracker.count_violations()

            engine_telemetry = {}
            if hasattr(self._policy_engine, "get_engine_telemetry"):
                engine_telemetry = getattr(
                    self._policy_engine, "get_engine_telemetry"
                )()

            return ProtectionStatistics(
                total_rules=total_rules,
                total_policies=total_policies,
                total_evaluations=engine_telemetry.get("total_evaluations", 0),
                allowed_requests=engine_telemetry.get("allowed_requests", 0),
                throttled_requests=engine_telemetry.get("throttled_requests", 0),
                rejected_requests=engine_telemetry.get("rejected_requests", 0),
                total_violations=total_violations,
                metrics={
                    "total_initializations": float(self._total_initializations),
                    "total_restarts": float(self._total_restarts),
                    "total_shutdowns": float(self._total_shutdowns),
                },
            )

    def capabilities(self) -> ProtectionCapabilities:
        """Get declared capabilities snapshot.

        Returns:
            ProtectionCapabilities: Immutable capabilities.
        """
        with self._lock:
            return self._capabilities

    def diagnostics(self) -> ProtectionDiagnostics:
        """Get diagnostic telemetry snapshot.

        Returns:
            ProtectionDiagnostics: Immutable diagnostics.
        """
        with self._lock:
            total_rules = self._rate_limiter.count_rules()
            total_policies = self._policy_engine.count_policies()
            total_violations = self._violation_tracker.count_violations()

            messages: Tuple[str, ...] = (
                f"Status: {self._status.value}",
                f"Registered Rules: {total_rules}",
                f"Registered Policies: {total_policies}",
                f"Active Violations: {total_violations}",
                f"Initializations: {self._total_initializations}",
                f"Restarts: {self._total_restarts}",
            )
            return ProtectionDiagnostics(
                state=self._status,
                registered_rules_count=total_rules,
                registered_policies_count=total_policies,
                active_violations_count=total_violations,
                timestamp=datetime.now(timezone.utc),
                thread_count=threading.active_count(),
                diagnostic_messages=messages,
                details={
                    "status": self._status.value,
                    "total_shutdowns": self._total_shutdowns,
                },
            )

    def get_rate_limiter(self) -> IRateLimiter:
        """Get encapsulated rate limiter.

        Returns:
            IRateLimiter: Rate limiter.
        """
        with self._lock:
            return self._rate_limiter

    def get_policy_engine(self) -> IPolicyEngine:
        """Get encapsulated policy engine.

        Returns:
            IPolicyEngine: Policy engine.
        """
        with self._lock:
            return self._policy_engine

    def get_violation_tracker(self) -> IViolationTracker:
        """Get encapsulated violation tracker.

        Returns:
            IViolationTracker: Violation tracker.
        """
        with self._lock:
            return self._violation_tracker
