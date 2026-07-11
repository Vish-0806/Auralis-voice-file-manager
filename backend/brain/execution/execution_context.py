"""Execution Context tracker for active Auralis execution sessions."""

from __future__ import annotations

import logging
from typing import Any, Dict
from .models import ExecutionContext as ContextModel


class ExecutionContext:
    """Maintains and updates live state details for an execution run."""

    def __init__(self, execution_id: str, logger: logging.Logger | None = None) -> None:
        """Initializes the ExecutionContext.

        Args:
            execution_id: Unique identifier for this execution run.
            logger: Optional custom logger for context operations.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._model = ContextModel(
            execution_id=execution_id,
            completed_steps=[],
        )

    @property
    def model(self) -> ContextModel:
        """Returns the underlying pydantic model representing this context."""
        return self._model

    def start_step(self, step_id: str, capability: str) -> None:
        """Updates context when a new step starts executing.

        Args:
            step_id: The ID of the step starting.
            capability: The name of the capability routed to.
        """
        self._model.current_step = step_id
        self._model.current_capability = capability
        self._logger.debug(
            "Execution step started",
            extra={"execution_id": self._model.execution_id, "step_id": step_id, "capability": capability},
        )

    def complete_step(self, step_id: str, result: Dict[str, Any]) -> None:
        """Updates context when a step completes successfully.

        Args:
            step_id: The ID of the completed step.
            result: Metadata result dictionary returned by the capability.
        """
        if step_id == self._model.current_step:
            self._model.current_step = None
            self._model.current_capability = None

        self._model.completed_steps.append(step_id)
        self._model.last_execution_result = result
        self._logger.debug(
            "Execution step completed",
            extra={"execution_id": self._model.execution_id, "step_id": step_id},
        )
