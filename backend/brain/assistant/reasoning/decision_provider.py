"""Decision Provider implementation for Auralis (Phase 13.4).

Aggregates DecisionCoordinator, PolicyManager, and DecisionEvaluator into a unified provider.
Exposes health diagnostics, performance statistics, and capabilities using constructor dependency injection only.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.reasoning.decision_coordinator import DecisionCoordinator
from brain.assistant.reasoning.decision_evaluator import DecisionEvaluator
from brain.assistant.reasoning.interfaces import (
    IDecisionCoordinator,
    IDecisionEvaluator,
    IDecisionPolicyManager,
    IDecisionProvider,
)
from brain.assistant.reasoning.models import (
    DecisionAction,
    DecisionHealth,
    DecisionPolicy,
    DecisionRequest,
    DecisionResult,
    DecisionStatistics,
)
from brain.assistant.reasoning.policy_manager import PolicyManager

logger = logging.getLogger(__name__)


class DecisionProvider(IDecisionProvider):
    """Aggregating provider for decision routing, policy evaluation, and candidate scoring."""

    def __init__(
        self,
        coordinator: Optional[IDecisionCoordinator] = None,
        policy_manager: Optional[IDecisionPolicyManager] = None,
        evaluator: Optional[IDecisionEvaluator] = None,
    ) -> None:
        """Initializes DecisionProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._policy_manager = policy_manager or PolicyManager(lock=self._lock)
        self._evaluator = evaluator or DecisionEvaluator(lock=self._lock)
        self._coordinator = coordinator or DecisionCoordinator(
            policy_manager=self._policy_manager,
            evaluator=self._evaluator,
            lock=self._lock,
        )

        self._initialized = False
        self._start_time: Optional[float] = None

        # Statistics metrics
        self._total_requests = 0
        self._direct_routed = 0
        self._ai_routed = 0
        self._planner_routed = 0
        self._clarifications_routed = 0
        self._confirmations_routed = 0
        self._rejections_routed = 0
        self._total_latency_ms = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def coordinator(self) -> IDecisionCoordinator:
        with self._lock:
            return self._coordinator

    @property
    def policy_manager(self) -> IDecisionPolicyManager:
        with self._lock:
            return self._policy_manager

    @property
    def evaluator(self) -> IDecisionEvaluator:
        with self._lock:
            return self._evaluator

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Core Decision Wrapper
    # ------------------------------------------------------------------

    def evaluate_request(
        self,
        request: DecisionRequest,
        policy: Optional[DecisionPolicy] = None,
    ) -> DecisionResult:
        """Evaluate request through coordinator while recording diagnostic statistics metrics."""
        t0 = time.time()
        res = self._coordinator.evaluate_request(request, policy)
        latency = (time.time() - t0) * 1000.0

        with self._lock:
            self._total_requests += 1
            self._total_latency_ms += latency

            if res.recommended_action == DecisionAction.DIRECT_EXECUTION:
                self._direct_routed += 1
            elif res.recommended_action == DecisionAction.AI_REQUIRED or res.requires_ai:
                self._ai_routed += 1
            elif res.recommended_action == DecisionAction.PLANNER_REQUIRED or res.requires_planner:
                self._planner_routed += 1
            elif res.recommended_action == DecisionAction.REJECT:
                self._rejections_routed += 1

            if res.requires_clarification:
                self._clarifications_routed += 1
            if res.requires_confirmation:
                self._confirmations_routed += 1

        return res

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize decision provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("DecisionProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down decision provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("DecisionProvider shutdown complete")

    def clear(self) -> None:
        """Reset decision provider statistics metrics."""
        with self._lock:
            self._total_requests = 0
            self._direct_routed = 0
            self._ai_routed = 0
            self._planner_routed = 0
            self._clarifications_routed = 0
            self._confirmations_routed = 0
            self._rejections_routed = 0
            self._total_latency_ms = 0.0

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_health(self) -> DecisionHealth:
        """Expose real-time diagnostic health snapshot."""
        with self._lock:
            subsystems = {
                "coordinator": self._coordinator is not None,
                "policy_manager": self._policy_manager is not None,
                "evaluator": self._evaluator is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("DecisionProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return DecisionHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> DecisionStatistics:
        """Expose aggregated performance statistics."""
        with self._lock:
            avg_latency = (self._total_latency_ms / self._total_requests) if self._total_requests > 0 else 0.0

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return DecisionStatistics(
                total_requests_evaluated=self._total_requests,
                direct_executions_routed=self._direct_routed,
                ai_required_routed=self._ai_routed,
                planner_required_routed=self._planner_routed,
                clarifications_routed=self._clarifications_routed,
                confirmations_routed=self._confirmations_routed,
                rejections_routed=self._rejections_routed,
                average_evaluation_latency_ms=avg_latency,
                uptime_seconds=uptime,
                metadata={},
            )
