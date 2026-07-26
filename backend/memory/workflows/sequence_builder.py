"""Stateless builder module for constructing deterministic WorkflowSequences."""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from memory.workflows.workflow_models import (
    WorkflowStepObservation,
    WorkflowSequence,
    WorkflowStatistics,
    ensure_utc
)


class SequenceBuilder:
    """Stateless builder class for constructing and validating WorkflowSequences."""

    def create_sequence(
        self,
        steps: list[WorkflowStepObservation],
        sequence_id: Optional[str] = None
    ) -> WorkflowSequence:
        """Converts step observations into a deterministically ordered WorkflowSequence."""
        if not steps:
            seq_id = sequence_id or str(uuid.uuid4())
            return WorkflowSequence(
                steps=[],
                sequence_id=seq_id,
                sequence_hash="empty_sequence",
                total_duration_ms=0.0
            )

        # 1. Deterministic sorting
        sorted_steps = self._sort_steps(steps)

        # 2. Sequence hash generation (deterministic based on step intents/targets)
        hash_input = ",".join(f"{s.intent}:{s.target or ''}" for s in sorted_steps)
        sequence_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        # 3. Calculate total duration
        total_duration = sum(s.duration_ms for s in sorted_steps)

        # 4. Generate sequence ID if not provided
        seq_id = sequence_id or str(uuid.uuid4())

        return WorkflowSequence(
            steps=sorted_steps,
            sequence_id=seq_id,
            sequence_hash=sequence_hash,
            total_duration_ms=total_duration
        )

    def _sort_steps(self, steps: list[WorkflowStepObservation]) -> list[WorkflowStepObservation]:
        """Sorts steps deterministically by started_at (falling back to timestamp), then step_id."""
        return sorted(
            steps,
            key=lambda s: (s.started_at or s.timestamp, s.step_id)
        )

    def _determine_success(self, steps: list[WorkflowStepObservation]) -> bool:
        """Determines if the step observations sequence is successful (all steps SUCCESS)."""
        if not steps:
            return False
        return all(s.status.upper() == "SUCCESS" for s in steps)

    def _calculate_statistics(
        self,
        steps: list[WorkflowStepObservation],
        sequence_hash: str
    ) -> WorkflowStatistics:
        """Computes workflow statistics for the given sequence steps."""
        if not steps:
            return WorkflowStatistics(
                sequence_hash=sequence_hash,
                total_observations=0,
                successful_executions=0,
                failed_executions=0,
                success_rate=0.0,
                average_duration_ms=0.0,
                last_observed=None
            )

        success = self._determine_success(steps)
        sorted_steps = self._sort_steps(steps)
        last_ts = sorted_steps[-1].timestamp if sorted_steps else None
        total_duration = sum(s.duration_ms for s in sorted_steps)

        return WorkflowStatistics(
            sequence_hash=sequence_hash,
            total_observations=1,
            successful_executions=1 if success else 0,
            failed_executions=0 if success else 1,
            success_rate=1.0 if success else 0.0,
            average_duration_ms=total_duration,
            last_observed=last_ts
        )
