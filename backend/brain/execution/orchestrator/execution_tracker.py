"""Execution Tracker for the Auralis Command Execution Orchestrator (Phase 12.3).

Responsible for:
- recording live execution context lifecycles
- tracking stage progressions, timings, failures, and retries
- generating ExecutionSummary snapshots
- aggregating diagnostic ExecutionStatistics
"""

import logging
import threading
from typing import Dict, List

from brain.execution.orchestrator.interfaces import IExecutionTracker
from brain.execution.orchestrator.orchestrator_models import (
    ExecutionContext,
    ExecutionResult,
    ExecutionStage,
    ExecutionStatistics,
    ExecutionSummary,
    OrchestrationStatus,
)

logger = logging.getLogger(__name__)


class ExecutionTracker(IExecutionTracker):
    """Thread-safe tracker recording stage executions, timing, failures, and statistics."""

    def __init__(self) -> None:
        """Initializes ExecutionTracker with thread lock and metrics storage."""
        self._lock = threading.RLock()
        self._active_contexts: Dict[str, ExecutionContext] = {}
        self._stage_records: Dict[str, List[ExecutionStage]] = {}

        self._total_orchestrations = 0
        self._successful_count = 0
        self._failed_count = 0
        self._aborted_count = 0
        self._total_duration_ms = 0.0
        self._orchestrations_by_mode: Dict[str, int] = {}

    def start_execution(self, context: ExecutionContext) -> str:
        """Record start of an execution context."""
        with self._lock:
            cid = context.context_id
            self._active_contexts[cid] = context
            self._stage_records[cid] = []
            self._total_orchestrations += 1

            mode_key = context.request.mode.value
            self._orchestrations_by_mode[mode_key] = self._orchestrations_by_mode.get(mode_key, 0) + 1

            return cid

    def record_stage(self, execution_id: str, stage: ExecutionStage) -> None:
        """Record a completed execution stage."""
        with self._lock:
            if execution_id in self._stage_records:
                self._stage_records[execution_id].append(stage)

    def complete_execution(
        self,
        execution_id: str,
        result: ExecutionResult,
    ) -> ExecutionSummary:
        """Record completion of execution and return an ExecutionSummary."""
        with self._lock:
            ctx = self._active_contexts.pop(execution_id, None)
            stages = self._stage_records.pop(execution_id, list(result.stages))

            if result.status == OrchestrationStatus.SUCCESS:
                self._successful_count += 1
            elif result.status in (OrchestrationStatus.CANCELLED, OrchestrationStatus.BLOCKED):
                self._aborted_count += 1
            else:
                self._failed_count += 1

            self._total_duration_ms += result.execution_time_ms

            completed_stages = sum(1 for s in stages if s.status == OrchestrationStatus.SUCCESS)

            return ExecutionSummary(
                execution_id=execution_id,
                prompt=ctx.request.raw_prompt if ctx else "",
                status=result.status,
                completed_stages=completed_stages,
                total_stages=len(stages),
                duration_ms=result.execution_time_ms,
                metadata=dict(result.metadata),
            )

    def get_statistics(self) -> ExecutionStatistics:
        """Return snapshot of aggregated execution statistics."""
        with self._lock:
            avg_dur = (self._total_duration_ms / self._total_orchestrations) if self._total_orchestrations > 0 else 0.0
            return ExecutionStatistics(
                total_orchestrations=self._total_orchestrations,
                successful_count=self._successful_count,
                failed_count=self._failed_count,
                aborted_count=self._aborted_count,
                average_duration_ms=avg_dur,
                orchestrations_by_mode=dict(self._orchestrations_by_mode),
                active_orchestrations=len(self._active_contexts),
                metadata={"thread_safety": "PROTECTED"},
            )

    def clear(self) -> None:
        """Reset execution statistics counters."""
        with self._lock:
            self._active_contexts.clear()
            self._stage_records.clear()
            self._total_orchestrations = 0
            self._successful_count = 0
            self._failed_count = 0
            self._aborted_count = 0
            self._total_duration_ms = 0.0
            self._orchestrations_by_mode.clear()
