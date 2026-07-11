"""Plan optimizer removing duplicates and optimizing step scheduling."""

from __future__ import annotations

import logging
from .models import ExecutionStep


class PlanOptimizer:
    """Optimizes execution steps by removing duplicates and flagging parallel paths."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PlanOptimizer.

        Args:
            logger: Optional custom logger for optimization diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def optimize_plan(self, steps: list[ExecutionStep]) -> list[ExecutionStep]:
        """Deduplicates and optimizes the execution sequence.

        Args:
            steps: The list of ordered execution steps.

        Returns:
            An optimized list of ExecutionSteps.
        """
        seen_keys: set[tuple[str, str | None]] = set()
        deduplicated: list[ExecutionStep] = []

        for step in steps:
            key = (step.intent.value, step.target)
            if key in seen_keys:
                self._logger.info(
                    "Removing duplicate step during optimization",
                    extra={"step_id": step.step_id, "intent": step.intent.value, "target": step.target},
                )
                continue
            seen_keys.add(key)
            deduplicated.append(step)

        optimized_steps: list[ExecutionStep] = []
        for step in deduplicated:
            updated_params = step.parameters.copy()
            updated_params["opt_parallel_group"] = 0
            
            if step.can_parallel:
                updated_params["opt_parallel_group"] = 1
            
            optimized_steps.append(
                ExecutionStep(
                    step_id=step.step_id,
                    intent=step.intent,
                    target=step.target,
                    parameters=updated_params,
                    can_parallel=step.can_parallel,
                )
            )

        self._logger.info(
            "Optimized plan successfully",
            extra={"original_count": len(steps), "optimized_count": len(optimized_steps)},
        )
        return optimized_steps
