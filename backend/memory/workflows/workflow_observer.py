"""Orchestrator for validating, building, and persisting workflow observations."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from memory.workflows.workflow_models import WorkflowStepObservation, WorkflowObservation
from memory.workflows.sequence_builder import SequenceBuilder


class WorkflowObserver:
    """Orchestrates the validation, construction, and persistence of workflow observations."""

    def __init__(
        self,
        sequence_builder: SequenceBuilder,
        observation_repository: Any,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initializes the WorkflowObserver with injected stateless dependencies."""
        self.sequence_builder = sequence_builder
        self.observation_repository = observation_repository
        self.logger = logger or logging.getLogger(__name__)

    async def observe(
        self,
        user_id: int,
        execution_id: str,
        steps: list[WorkflowStepObservation],
        context_metadata: Optional[dict[str, Any]] = None
    ) -> WorkflowObservation:
        """Validates steps, builds a WorkflowObservation using SequenceBuilder, and saves it."""
        self._validate_steps(steps)

        # Determine overall success
        success = self.sequence_builder._determine_success(steps)

        # Use latest step timestamp as the overall observation timestamp
        sorted_steps = self.sequence_builder._sort_steps(steps)
        timestamp = sorted_steps[-1].timestamp if sorted_steps else datetime.now(timezone.utc)

        return await self.observe_execution(
            user_id=user_id,
            execution_id=execution_id,
            steps=steps,
            success=success,
            timestamp=timestamp,
            context_metadata=context_metadata
        )

    async def observe_execution(
        self,
        user_id: int,
        execution_id: str,
        steps: list[WorkflowStepObservation],
        success: bool,
        timestamp: datetime,
        context_metadata: Optional[dict[str, Any]] = None
    ) -> WorkflowObservation:
        """Builds and persists a WorkflowObservation with explicit execution results."""
        observation = self._build_observation(
            user_id=user_id,
            execution_id=execution_id,
            steps=steps,
            success=success,
            timestamp=timestamp,
            context_metadata=context_metadata
        )

        # Save to repository
        await self.observation_repository.save_observation(observation)

        self.logger.info(
            "Workflow observation recorded",
            extra={
                "user_id": user_id,
                "execution_id": execution_id,
                "sequence_hash": observation.sequence.sequence_hash,
                "success": success
            }
        )
        return observation

    def _validate_steps(self, steps: list[WorkflowStepObservation]) -> None:
        """Validates that step observations are non-empty, unique, and timezone-aware."""
        if not steps:
            raise ValueError("Steps list cannot be empty for workflow observation.")

        seen_ids = set()
        for step in steps:
            # Check duplicate IDs
            if step.step_id in seen_ids:
                raise ValueError(f"Duplicate step ID detected: '{step.step_id}'")
            seen_ids.add(step.step_id)

            # Check timezone-aware timestamp
            if step.timestamp is None or step.timestamp.tzinfo is None:
                raise ValueError(f"Step '{step.step_id}' has naive or missing timestamp.")

    def _build_observation(
        self,
        user_id: int,
        execution_id: str,
        steps: list[WorkflowStepObservation],
        success: bool,
        timestamp: datetime,
        context_metadata: Optional[dict[str, Any]] = None
    ) -> WorkflowObservation:
        """Constructs a validated WorkflowObservation object."""
        self._validate_steps(steps)

        if timestamp is None or timestamp.tzinfo is None:
            raise ValueError("Workflow observation timestamp must be timezone-aware.")

        sequence = self.sequence_builder.create_sequence(steps)

        return WorkflowObservation(
            user_id=user_id,
            execution_id=execution_id,
            sequence=sequence,
            success=success,
            timestamp=timestamp,
            context_metadata=context_metadata or {}
        )
