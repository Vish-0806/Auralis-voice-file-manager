"""Dependency resolver performing topological sorting to resolve task execution order."""

from __future__ import annotations

import logging
from collections import defaultdict
from .models import ExecutionStep, ExecutionSequence


class DependencyResolver:
    """Resolves dependencies between execution steps and detects circular relations."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the DependencyResolver.

        Args:
            logger: Optional custom logger for dependency resolution.
        """
        self._logger = logger or logging.getLogger(__name__)

    def resolve_order(self, sequence: ExecutionSequence) -> list[ExecutionStep]:
        """Resolves task order using topological sort and checks for circular dependencies.

        Args:
            sequence: The ExecutionSequence containing steps and dependencies.

        Returns:
            A list of ExecutionSteps sorted in dependency order.

        Raises:
            ValueError: If a circular dependency is detected.
        """
        steps_map = {step.step_id: step for step in sequence.steps}
        adj_list = defaultdict(list)
        in_degree = defaultdict(int)

        for step_id in steps_map:
            in_degree[step_id] = 0

        for dep in sequence.dependencies:
            step_id = dep.step_id
            if step_id not in steps_map:
                continue

            for parent_id in dep.depends_on:
                if parent_id not in steps_map:
                    continue
                adj_list[parent_id].append(step_id)
                in_degree[step_id] += 1

        queue = [step_id for step_id, deg in in_degree.items() if deg == 0]
        ordered_step_ids: list[str] = []

        while queue:
            queue.sort()
            curr = queue.pop(0)
            ordered_step_ids.append(curr)

            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_step_ids) != len(steps_map):
            cycle_nodes = [step_id for step_id, deg in in_degree.items() if deg > 0]
            self._logger.error("Circular dependency detected", extra={"cycle_nodes": cycle_nodes})
            raise ValueError(f"Circular dependency detected between steps: {cycle_nodes}")

        ordered_steps = [steps_map[step_id] for step_id in ordered_step_ids]
        self._logger.info(
            "Resolved dependency order successfully",
            extra={"ordered_steps": [s.step_id for s in ordered_steps]},
        )
        return ordered_steps
