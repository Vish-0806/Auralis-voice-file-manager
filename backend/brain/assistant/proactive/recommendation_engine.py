"""Recommendation Engine implementation for Auralis (Phase 13.8).

Generates deterministic recommendations, reminders, assistant suggestions, and contextual recommendations.
Performs priority scoring, recommendation ranking, and duplicate suppression without LLM inference.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Dict, List, Optional, Set

from brain.assistant.proactive.interfaces import IRecommendationEngine
from brain.assistant.proactive.models import (
    ProactiveContext,
    ProactiveEvent,
    ProactiveRecommendation,
    ProactiveSuggestion,
    SuggestionPriority,
    SuggestionType,
)

logger = logging.getLogger(__name__)

_PRIORITY_WEIGHTS = {
    SuggestionPriority.MANDATORY: 5.0,
    SuggestionPriority.CRITICAL: 4.0,
    SuggestionPriority.HIGH: 3.0,
    SuggestionPriority.MEDIUM: 2.0,
    SuggestionPriority.LOW: 1.0,
}


class RecommendationEngine(IRecommendationEngine):
    """Thread-safe engine for generating, scoring, ranking, and deduplicating proactive recommendations."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._seen_titles: Set[str] = set()

        # Metrics
        self._total_generated = 0
        self._duplicates_suppressed = 0

    @property
    def total_recommendations_generated(self) -> int:
        with self._lock:
            return self._total_generated

    @property
    def duplicates_suppressed_count(self) -> int:
        with self._lock:
            return self._duplicates_suppressed

    def generate_recommendations(
        self,
        context: ProactiveContext,
        event: Optional[ProactiveEvent] = None,
    ) -> List[ProactiveRecommendation]:
        """Generate ranked, deduplicated proactive recommendations."""
        with self._lock:
            suggestions: List[ProactiveSuggestion] = []

            # 1. Idle time reminder rule
            if context.idle_time_seconds >= 300.0:
                suggestions.append(
                    ProactiveSuggestion(
                        title="System Idle Reminder",
                        description="System has been idle for over 5 minutes. Consider organizing your active workspace.",
                        suggestion_type=SuggestionType.REMINDER,
                        priority=SuggestionPriority.LOW,
                        score=0.75,
                        action_key="organize_workspace",
                    )
                )

            # 2. Dialogue clarification recommendation
            if context.last_decision_action == "CLARIFICATION_REQUIRED":
                suggestions.append(
                    ProactiveSuggestion(
                        title="Provide Command Clarification",
                        description="The assistant requires clarification on your recent command.",
                        suggestion_type=SuggestionType.CLARIFICATION,
                        priority=SuggestionPriority.HIGH,
                        score=0.95,
                        action_key="provide_clarification",
                    )
                )

            # 3. Event-driven recommendation
            if event is not None:
                suggestions.append(
                    ProactiveSuggestion(
                        title=f"Follow-up for {event.event_type}",
                        description=f"Action suggested in response to event '{event.event_type}' from {event.source}.",
                        suggestion_type=SuggestionType.ACTION_SUGGESTION,
                        priority=SuggestionPriority.MEDIUM,
                        score=0.85,
                        action_key=f"handle_{event.event_type.lower()}",
                        payload=event.payload,
                    )
                )

            # 4. Default contextual suggestion
            if not suggestions:
                suggestions.append(
                    ProactiveSuggestion(
                        title="Contextual Assistant Optimization",
                        description="No immediate actions required. Assistant standing by.",
                        suggestion_type=SuggestionType.RECOMMENDATION,
                        priority=SuggestionPriority.LOW,
                        score=0.5,
                    )
                )

            # Deduplicate & Rank by priority weight + score
            recommendations: List[ProactiveRecommendation] = []
            for sug in suggestions:
                if sug.title in self._seen_titles and sug.priority != SuggestionPriority.MANDATORY:
                    self._duplicates_suppressed += 1
                    logger.debug("Suppressed duplicate recommendation title='%s'", sug.title)
                    continue

                self._seen_titles.add(sug.title)
                self._total_generated += 1

                weight = _PRIORITY_WEIGHTS.get(sug.priority, 1.0)
                final_confidence = min(1.0, (sug.score * weight) / 5.0)

                rec = ProactiveRecommendation(
                    suggestion=sug,
                    reasoning=sug.description,
                    confidence=final_confidence,
                    cooldown_seconds=60.0,
                    created_at=datetime.now(timezone.utc),
                )
                recommendations.append(rec)

            # Sort recommendations descending by confidence
            recommendations.sort(key=lambda r: r.confidence, reverse=True)

            logger.info("Generated %d proactive recommendations", len(recommendations))
            return recommendations

    def clear(self) -> None:
        """Reset recommendation engine state."""
        with self._lock:
            self._seen_titles.clear()
            self._total_generated = 0
            self._duplicates_suppressed = 0
