"""Statistics Manager for the Auralis Brain Runtime (Phase 9.7).

Aggregates diagnostic statistics across all 6 subsystem runtimes into a unified BrainRuntimeStatistics snapshot.
"""

import logging
import threading
from typing import Any, Dict, Optional

from brain.runtime.brain_models import (
    BrainRuntimeStatistics,
    RuntimeComponent,
)
from brain.runtime.dependency_registry import DependencyRegistry

logger = logging.getLogger(__name__)


class _MutableBrainStats:
    """Internal mutable counter accumulator."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_pipeline_ms: float = 0.0
        self.peak_concurrent_requests: int = 0
        self._active_requests: int = 0

    def record_start(self) -> None:
        self.total_requests += 1
        self._active_requests += 1
        if self._active_requests > self.peak_concurrent_requests:
            self.peak_concurrent_requests = self._active_requests

    def record_complete(self, duration_ms: float, success: bool = True) -> None:
        self._active_requests = max(0, self._active_requests - 1)
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_pipeline_ms += duration_ms


class StatisticsManager:
    """Thread-safe statistics manager for the Auralis Brain architecture.

    Responsibilities:
    - Track global request counts, average latency, and concurrency.
    - Query and aggregate statistics from all 6 subsystem runtimes.
    """

    def __init__(self, registry: Optional[DependencyRegistry] = None) -> None:
        self._lock = threading.RLock()
        self._registry = registry or DependencyRegistry()
        self._stats = _MutableBrainStats()
        logger.debug("StatisticsManager initialized")

    def record_request_start(self) -> None:
        """Increment active request count and total requests."""
        with self._lock:
            self._stats.record_start()

    def record_request_complete(self, duration_ms: float, success: bool = True) -> None:
        """Record completed request duration and outcome.

        Args:
            duration_ms: Total pipeline latency in ms.
            success: Whether the request completed successfully.
        """
        with self._lock:
            self._stats.record_complete(duration_ms, success)
            logger.info("Statistics Updated: requests=%d avg_ms=%.1f", self._stats.total_requests, self._calc_avg())

    def get_statistics(self) -> BrainRuntimeStatistics:
        """Query and aggregate complete statistics across all subsystems.

        Returns:
            Immutable :class:`BrainRuntimeStatistics` snapshot.
        """
        with self._lock:
            subsystem_stats: Dict[str, Dict[str, Any]] = {}
            for comp in RuntimeComponent:
                if comp == RuntimeComponent.BRAIN:
                    continue
                name = comp.value
                subsystem_stats[name] = self.get_subsystem_statistics(comp)

            avg_ms = self._calc_avg()

            return BrainRuntimeStatistics(
                total_requests=self._stats.total_requests,
                successful_requests=self._stats.successful_requests,
                failed_requests=self._stats.failed_requests,
                average_pipeline_ms=round(avg_ms, 3),
                subsystem_stats=subsystem_stats,
                peak_concurrent_requests=self._stats.peak_concurrent_requests,
            )

    def get_subsystem_statistics(self, component: RuntimeComponent) -> Dict[str, Any]:
        """Query statistics dict from a single subsystem.

        Args:
            component: Target component.

        Returns:
            Dict of statistics key-values.
        """
        name = component.value
        with self._lock:
            instance = self._registry.get(component)
            if instance is None:
                return {"status": "NOT_REGISTERED"}

            try:
                if hasattr(instance, "get_statistics") and callable(instance.get_statistics):
                    raw = instance.get_statistics()
                    if hasattr(raw, "model_dump"):
                        return raw.model_dump()
                    elif hasattr(raw, "dict"):
                        return raw.dict()
                    elif isinstance(raw, dict):
                        return raw
                elif hasattr(instance, "statistics"):
                    st = getattr(instance, "statistics")
                    if isinstance(st, dict):
                        return st
                return {"status": "AVAILABLE"}
            except Exception as exc:
                logger.warning("StatisticsManager: Failed to fetch stats for %s: %s", name, exc)
                return {"status": "ERROR", "error": str(exc)}

    def clear(self) -> None:
        """Reset all global statistics counters to zero."""
        with self._lock:
            self._stats = _MutableBrainStats()
            logger.debug("StatisticsManager cleared")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _calc_avg(self) -> float:
        completed = self._stats.successful_requests + self._stats.failed_requests
        return self._stats.total_pipeline_ms / completed if completed > 0 else 0.0
