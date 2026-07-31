"""DefaultTimeoutManager implementation for tracking timeout limits (Phase 10.7).

Evaluates execution, plan, and step timeouts, calculates elapsed and remaining time,
and returns TimeoutState snapshots without threading or asyncio background tasks.
"""

import time
import logging
from typing import Dict

from brain.ai.resilience.interfaces import TimeoutManagerInterface
from brain.ai.resilience.resilience_models import TimeoutState, TimeoutStatus

logger = logging.getLogger(__name__)


class DefaultTimeoutManager(TimeoutManagerInterface):
    """Tracks timeout timers and evaluates elapsed/remaining time."""

    def __init__(self) -> None:
        self._timers: Dict[str, Dict[str, float]] = {}

    def start_timer(self, target_id: str, timeout_seconds: float) -> TimeoutState:
        """Start tracking a target timeout."""
        start_time = time.perf_counter()
        self._timers[target_id] = {
            "start_time": start_time,
            "timeout_seconds": timeout_seconds,
        }
        return self.check_timeout(target_id)

    def check_timeout(self, target_id: str) -> TimeoutState:
        """Check current elapsed and remaining time for a target."""
        if target_id not in self._timers:
            return TimeoutState(
                target_id=target_id,
                start_time=time.perf_counter(),
                timeout_seconds=0.0,
                elapsed_seconds=0.0,
                remaining_seconds=0.0,
                status=TimeoutStatus.EXPIRED,
            )

        timer_info = self._timers[target_id]
        start_time = timer_info["start_time"]
        timeout_seconds = timer_info["timeout_seconds"]

        elapsed = round(time.perf_counter() - start_time, 3)
        remaining = max(0.0, round(timeout_seconds - elapsed, 3))

        if elapsed >= timeout_seconds:
            status = TimeoutStatus.EXPIRED
        elif remaining <= (timeout_seconds * 0.2):
            status = TimeoutStatus.WARNING
        else:
            status = TimeoutStatus.ACTIVE

        return TimeoutState(
            target_id=target_id,
            start_time=start_time,
            timeout_seconds=timeout_seconds,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
            status=status,
        )

    def stop_timer(self, target_id: str) -> None:
        """Stop tracking a target timer."""
        self._timers.pop(target_id, None)
