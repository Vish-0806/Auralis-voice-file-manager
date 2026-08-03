"""Proactive Provider implementation for Auralis (Phase 13.8).

Aggregates ProactiveCoordinator, RecommendationEngine, NotificationManager, and RuleEvaluator into a unified provider.
Exposes health diagnostics, performance statistics, capabilities, and diagnostics using constructor dependency injection only.
No mutable global singletons. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import List, Optional

from brain.assistant.proactive.interfaces import (
    INotificationManager,
    IProactiveCoordinator,
    IProactiveProvider,
    IRecommendationEngine,
    IRuleEvaluator,
)
from brain.assistant.proactive.models import (
    ProactiveCapabilities,
    ProactiveHealth,
    ProactiveStatistics,
)
from brain.assistant.proactive.notification_manager import NotificationManager
from brain.assistant.proactive.proactive_coordinator import ProactiveCoordinator
from brain.assistant.proactive.recommendation_engine import RecommendationEngine
from brain.assistant.proactive.rule_evaluator import RuleEvaluator

logger = logging.getLogger(__name__)


class ProactiveProvider(IProactiveProvider):
    """Aggregating provider for proactive behavior evaluation, recommendation generation, and notification management."""

    def __init__(
        self,
        coordinator: Optional[IProactiveCoordinator] = None,
        recommendation_engine: Optional[IRecommendationEngine] = None,
        notification_manager: Optional[INotificationManager] = None,
        rule_evaluator: Optional[IRuleEvaluator] = None,
    ) -> None:
        """Initializes ProactiveProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._recommendation_engine = recommendation_engine or RecommendationEngine(lock=self._lock)
        self._notification_manager = notification_manager or NotificationManager(lock=self._lock)
        self._rule_evaluator = rule_evaluator or RuleEvaluator(lock=self._lock)
        self._coordinator = coordinator or ProactiveCoordinator(
            recommendation_engine=self._recommendation_engine,
            notification_manager=self._notification_manager,
            rule_evaluator=self._rule_evaluator,
            lock=self._lock,
        )

        self._initialized = False
        self._start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def coordinator(self) -> IProactiveCoordinator:
        with self._lock:
            return self._coordinator

    @property
    def recommendation_engine(self) -> IRecommendationEngine:
        with self._lock:
            return self._recommendation_engine

    @property
    def notification_manager(self) -> INotificationManager:
        with self._lock:
            return self._notification_manager

    @property
    def rule_evaluator(self) -> IRuleEvaluator:
        with self._lock:
            return self._rule_evaluator

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("ProactiveProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("ProactiveProvider shutdown complete")

    def clear(self) -> None:
        """Reset sub-managers and metrics."""
        with self._lock:
            if hasattr(self._recommendation_engine, "clear"):
                self._recommendation_engine.clear()  # type: ignore[union-attr]
            if hasattr(self._notification_manager, "clear"):
                self._notification_manager.clear()  # type: ignore[union-attr]
            if hasattr(self._rule_evaluator, "clear"):
                self._rule_evaluator.clear()  # type: ignore[union-attr]
            if hasattr(self._coordinator, "clear"):
                self._coordinator.clear()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_capabilities(self) -> ProactiveCapabilities:
        """Expose proactive capabilities specification."""
        return ProactiveCapabilities()

    def get_health(self) -> ProactiveHealth:
        """Expose real-time diagnostic health report."""
        with self._lock:
            subsystems = {
                "coordinator": self._coordinator is not None,
                "recommendation_engine": self._recommendation_engine is not None,
                "notification_manager": self._notification_manager is not None,
                "rule_evaluator": self._rule_evaluator is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("ProactiveProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return ProactiveHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> ProactiveStatistics:
        """Expose aggregated proactive performance metrics."""
        with self._lock:
            total_evals = getattr(self._coordinator, "evaluation_count", 0)
            recs_gen = getattr(self._recommendation_engine, "total_recommendations_generated", 0)
            notifs_created = getattr(self._notification_manager, "total_created_count", 0)
            notifs_dismissed = getattr(self._notification_manager, "dismissed_count", 0)
            notifs_archived = getattr(self._notification_manager, "archived_count", 0)
            dups = getattr(self._recommendation_engine, "duplicates_suppressed_count", 0)
            cooldowns = getattr(self._rule_evaluator, "cooldowns_enforced_count", 0)

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return ProactiveStatistics(
                total_evaluations=total_evals,
                total_recommendations_generated=recs_gen,
                total_notifications_created=notifs_created,
                notifications_dismissed=notifs_dismissed,
                notifications_archived=notifs_archived,
                duplicates_suppressed=dups,
                cooldowns_enforced=cooldowns,
                average_evaluation_latency_ms=0.0,
                uptime_seconds=uptime,
                metadata={},
            )
