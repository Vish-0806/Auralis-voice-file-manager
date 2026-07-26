"""Routine Pattern Detector mining repeating user execution behaviors."""

import logging
from datetime import datetime, timezone
from typing import Any, List
from memory.routines.models import RoutineCandidate

logger = logging.getLogger(__name__)


class RoutinePatternDetector:
    """Discovers recurring sequences of actions and maps them to routine suggestions."""

    def __init__(self, min_support: int = 3, min_confidence: float = 0.6) -> None:
        """Initializes the pattern detector with frequency and confidence threshold limits."""
        self.min_support = min_support
        self.min_confidence = min_confidence

    def detect_candidates(self, executions: list[Any]) -> list[RoutineCandidate]:
        """Runs sequence analysis and returns matching RoutineCandidate models."""
        if len(executions) < self.min_support:
            return []

        actions = [getattr(e, "action", "") for e in executions]
        freq = {}
        occurrence_times = {}

        # 1. Sequence mining and frequency tracking
        for i in range(len(actions) - 1):
            pair = (actions[i], actions[i+1])
            freq[pair] = freq.get(pair, 0) + 1
            if pair not in occurrence_times:
                occurrence_times[pair] = []

            # Retrieve timestamp safely
            t = (
                getattr(executions[i], "created_at", None)
                or getattr(executions[i], "timestamp", None)
                or datetime.now(timezone.utc)
            )
            occurrence_times[pair].append(t)

        candidates = []
        for pair, count in freq.items():
            # 2. Threshold filtering check
            if count < self.min_support:
                continue

            # 3. Confidence computation P(action2 | action1)
            prefix_count = actions.count(pair[0])
            confidence = count / prefix_count if prefix_count > 0 else 0.0
            if confidence < self.min_confidence:
                continue

            # 4. Temporal delta interval computation
            times = sorted(occurrence_times[pair])
            if len(times) >= 2:
                intervals = [(times[j+1] - times[j]).total_seconds() for j in range(len(times) - 1)]
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 0.0

            candidates.append(
                RoutineCandidate(
                    trigger_event=pair[0],
                    action_sequence={"steps": [{"action": pair[1], "parameters": {}}]},
                    confidence_score=confidence,
                    frequency=count,
                    avg_interval_seconds=avg_interval
                )
            )

        # Deterministic sort: confidence desc, frequency desc, trigger name asc
        candidates.sort(key=lambda c: (-c.confidence_score, -c.frequency, c.trigger_event))
        return candidates
