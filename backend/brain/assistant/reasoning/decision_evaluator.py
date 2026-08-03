"""Decision Evaluator implementation for Auralis (Phase 13.4).

Scores decision candidates, resolves conflicts, determines the highest priority candidate,
and validates routing consistency without AI calls. Thread-safe using threading.RLock().
"""

import logging
import threading
from typing import List, Optional

from brain.assistant.reasoning.exceptions import DecisionRoutingError
from brain.assistant.reasoning.interfaces import IDecisionEvaluator
from brain.assistant.reasoning.models import (
    DecisionCandidate,
    DecisionContext,
    DecisionPriority,
)

logger = logging.getLogger(__name__)

_PRIORITY_WEIGHTS = {
    DecisionPriority.IMMEDIATE: 1.5,
    DecisionPriority.CRITICAL: 1.4,
    DecisionPriority.HIGH: 1.2,
    DecisionPriority.MEDIUM: 1.0,
    DecisionPriority.LOW: 0.8,
}


class DecisionEvaluator(IDecisionEvaluator):
    """Thread-safe candidate scoring and conflict resolution evaluator."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def evaluate_candidates(
        self,
        candidates: List[DecisionCandidate],
        context: DecisionContext,
    ) -> DecisionCandidate:
        """Score candidates, resolve action conflicts, and return the winning decision candidate."""
        if not candidates:
            raise DecisionRoutingError("Cannot evaluate candidates: empty candidate list provided")

        with self._lock:
            best_candidate: Optional[DecisionCandidate] = None
            best_weighted_score = -1.0

            for cand in candidates:
                weight = _PRIORITY_WEIGHTS.get(cand.priority, 1.0)
                weighted_score = cand.score * weight

                # Bonus for context match
                if context.execution_ready and cand.action.name == "DIRECT_EXECUTION":
                    weighted_score += 0.1

                if weighted_score > best_weighted_score:
                    best_weighted_score = weighted_score
                    best_candidate = cand

            if best_candidate is None:
                best_candidate = candidates[0]

            logger.debug(
                "Selected decision candidate id=%s action=%s score=%.2f",
                best_candidate.candidate_id,
                best_candidate.action,
                best_weighted_score,
            )
            return best_candidate
