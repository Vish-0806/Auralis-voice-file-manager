"""DefaultRetryManager implementation for retry calculations (Phase 10.7).

Calculates fixed and exponential backoff delays, tracks retry history, and evaluates
retry eligibility without executing sleeps or async background tasks.
"""

import logging
from typing import Dict, List, Optional

from brain.ai.resilience.interfaces import RetryManagerInterface
from brain.ai.resilience.resilience_models import (
    RetryAttempt,
    RetryPolicy,
    RetryStrategy,
)

logger = logging.getLogger(__name__)


class DefaultRetryManager(RetryManagerInterface):
    """Calculates retry delays and evaluates policy eligibility."""

    def __init__(self, default_policy: Optional[RetryPolicy] = None) -> None:
        self.default_policy = default_policy or RetryPolicy()
        self._history: Dict[str, List[RetryAttempt]] = {}

    def evaluate_retry(
        self,
        attempt_number: int,
        policy: Optional[RetryPolicy] = None,
        reason: str = "",
        target_id: str = "default",
    ) -> Optional[RetryAttempt]:
        """Calculate next retry attempt or return None if max_retries exceeded.

        Args:
            attempt_number: Current retry attempt count (1-indexed).
            policy: Optional RetryPolicy override.
            reason: Reason description for retry calculation.
            target_id: Operation target identifier.

        Returns:
            RetryAttempt model if eligible, else None.
        """
        active_policy = policy or self.default_policy

        if attempt_number > active_policy.max_retries:
            logger.debug(
                f"Target '{target_id}': Attempt {attempt_number} exceeds max_retries ({active_policy.max_retries})."
            )
            return None

        delay_seconds = self.calculate_delay(attempt_number, active_policy)

        attempt = RetryAttempt(
            attempt_number=attempt_number,
            delay_seconds=delay_seconds,
            reason=reason or "Failure evaluation retry",
        )

        if target_id not in self._history:
            self._history[target_id] = []
        self._history[target_id].append(attempt)

        return attempt

    def calculate_delay(self, attempt_number: int, policy: RetryPolicy) -> float:
        """Calculate delay in seconds based on policy strategy."""
        if policy.strategy == RetryStrategy.FIXED:
            delay = policy.base_delay_seconds
        elif policy.strategy == RetryStrategy.LINEAR:
            delay = policy.base_delay_seconds * attempt_number
        else:  # EXPONENTIAL_BACKOFF
            multiplier = policy.backoff_multiplier ** (attempt_number - 1)
            delay = policy.base_delay_seconds * multiplier

        return min(policy.max_delay_seconds, round(delay, 3))

    def get_history(self, target_id: str = "default") -> List[RetryAttempt]:
        """Retrieve recorded retry history for a target."""
        return list(self._history.get(target_id, []))
