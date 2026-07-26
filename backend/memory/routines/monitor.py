"""Routine Runtime Monitor tracking success rates, run times, and failures."""

import logging
from typing import Any, Dict, List
from memory.routines.models import RoutineRunMetric

logger = logging.getLogger(__name__)


class RoutineRuntimeMonitor:
    """Monitors performance benchmarks, success thresholds, and optimization hints."""

    def __init__(self) -> None:
        self._metrics: Dict[int, List[RoutineRunMetric]] = {}

    def record_execution(self, routine_id: int, duration_ms: float, success: bool) -> RoutineRunMetric:
        """Records a single routine execution performance result."""
        metric = RoutineRunMetric(
            routine_id=routine_id,
            duration_ms=duration_ms,
            success=success
        )
        if routine_id not in self._metrics:
            self._metrics[routine_id] = []
        self._metrics[routine_id].append(metric)

        logger.info(
            f"Recorded routine {routine_id} execution: success={success}, duration={duration_ms}ms"
        )
        return metric

    def get_statistics(self, routine_id: int) -> Dict[str, Any]:
        """Aggregates execution counts, success ratios, and optimization advice."""
        metrics_list = self._metrics.get(routine_id, [])
        if not metrics_list:
            return {
                "total_runs": 0,
                "success_rate": 1.0,
                "avg_duration_ms": 0.0,
                "failures_count": 0,
                "optimisation_opportunities": []
            }

        total_runs = len(metrics_list)
        success_count = sum(1 for m in metrics_list if m.success)
        failures_count = total_runs - success_count
        avg_dur = sum(m.duration_ms for m in metrics_list) / total_runs

        # Heuristic optimization tips
        opps = []
        if avg_dur > 1500.0:
            opps.append("Sequence averages over 1500ms; parallel execution tags recommended.")
        if success_count / total_runs < 0.7:
            opps.append("Success rate is below 70%; check parameters or capability configs.")

        return {
            "total_runs": total_runs,
            "success_rate": success_count / total_runs,
            "avg_duration_ms": avg_dur,
            "failures_count": failures_count,
            "optimisation_opportunities": opps
        }
