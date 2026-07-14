"""Confidence Calculator for Routine suggestions."""

import logging

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Calculates confidence scores for recurring action patterns based on frequency and success rates."""

    @staticmethod
    def calculate(occurrences: int, total_sessions: int, success_rate: float) -> float:
        """Computes a normalized confidence score between 0.0 and 1.0.

        Args:
            occurrences: Frequency of pattern repeats.
            total_sessions: Total grouping episodes found in history.
            success_rate: Ratio of success execution runs in sequence.

        Returns:
            Confidence score float between 0.0 and 1.0.
        """
        if total_sessions <= 0:
            return 0.0

        # Support ratio (how common this routine is relative to total user sessions, min 3 sessions to scale)
        support = occurrences / max(3, total_sessions)

        # Base confidence calculation
        score = support * success_rate

        # Capped between 0.0 and 1.0
        score = max(0.0, min(1.0, score))

        logger.debug(
            f"Calculated confidence score: {score:.2f} (repeats: {occurrences}, sessions: {total_sessions}, success: {success_rate:.2f})"
        )
        return float(round(score, 2))
