"""Proactive Coordinator implementation for Auralis (Phase 13.8).

Coordinates proactive behavior evaluation across Assistant, Conversation, Dialogue, Decision, Memory,
Voice, Execution, Automation, and Analytics runtimes.
Does NOT execute workflows or OS commands. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, Optional

from brain.assistant.proactive.interfaces import (
    INotificationManager,
    IProactiveCoordinator,
    IRecommendationEngine,
    IRuleEvaluator,
)
from brain.assistant.proactive.models import (
    EvaluationResult,
    ProactiveContext,
    ProactiveEvaluation,
    ProactiveEvent,
    ProactiveNotification,
    ProactiveRecommendation,
)
from brain.assistant.proactive.notification_manager import NotificationManager
from brain.assistant.proactive.recommendation_engine import RecommendationEngine
from brain.assistant.proactive.rule_evaluator import RuleEvaluator

logger = logging.getLogger(__name__)


class ProactiveCoordinator(IProactiveCoordinator):
    """Thread-safe coordinator executing proactive behavior evaluation."""

    def __init__(
        self,
        recommendation_engine: Optional[IRecommendationEngine] = None,
        notification_manager: Optional[INotificationManager] = None,
        rule_evaluator: Optional[IRuleEvaluator] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self._lock = lock or threading.RLock()
        self._recommendation_engine = recommendation_engine or RecommendationEngine(lock=self._lock)
        self._notification_manager = notification_manager or NotificationManager(lock=self._lock)
        self._rule_evaluator = rule_evaluator or RuleEvaluator(lock=self._lock)

        self._evaluation_count = 0

    @property
    def evaluation_count(self) -> int:
        with self._lock:
            return self._evaluation_count

    def evaluate_proactive_behavior(
        self,
        event: Optional[ProactiveEvent] = None,
        context: Optional[ProactiveContext] = None,
        runtimes: Optional[Dict[str, Any]] = None,
    ) -> ProactiveEvaluation:
        """Evaluate whether the assistant should proactively notify or suggest an action."""
        with self._lock:
            self._evaluation_count += 1
            ctx = context or ProactiveContext()
            runtimes_map = runtimes or {}

            # Collect runtime state if provided
            if "dialogue_runtime" in runtimes_map:
                try:
                    d_health = runtimes_map["dialogue_runtime"].get_health()
                    ctx = ProactiveContext(
                        session_id=ctx.session_id,
                        user_id=ctx.user_id,
                        active_dialogue_state=d_health.status,
                        last_decision_action=ctx.last_decision_action,
                        idle_time_seconds=ctx.idle_time_seconds,
                        context_variables=ctx.context_variables,
                    )
                except Exception as exc:
                    logger.debug("Failed to inspect dialogue_runtime in ProactiveCoordinator: %s", exc)

            # Generate proactive recommendations
            recs = self._recommendation_engine.generate_recommendations(ctx, event)
            top_rec: Optional[ProactiveRecommendation] = recs[0] if recs else None

            # Create notification object if recommendation exists
            created_notif: Optional[ProactiveNotification] = None
            if top_rec:
                created_notif = self._notification_manager.create_notification(
                    title=top_rec.suggestion.title,
                    message=top_rec.suggestion.description,
                    notification_type="RECOMMENDATION",
                    priority=top_rec.suggestion.priority.value,
                )

            res_outcome = EvaluationResult.TRIGGERED if recs else EvaluationResult.NO_ACTION

            evaluation = ProactiveEvaluation(
                result=res_outcome,
                recommendation=top_rec,
                notification=created_notif,
                reason=f"Evaluated {len(recs)} proactive recommendations",
                evaluated_at=datetime.now(timezone.utc),
            )

            logger.info("Evaluated proactive behavior result=%s (recs=%d)", evaluation.result, len(recs))
            return evaluation

    def clear(self) -> None:
        """Reset evaluation metrics."""
        with self._lock:
            self._evaluation_count = 0
