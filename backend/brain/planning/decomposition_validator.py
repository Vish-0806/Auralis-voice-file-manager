"""Decomposition validator verifying objective graph cycle safety in Auralis."""

from __future__ import annotations

import logging
from .objective_graph import ObjectiveGraph


class DecompositionValidator:
    """Validates the structural integrity and dependency safety of ObjectiveGraphs."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes DecompositionValidator.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def validate(self, graph: ObjectiveGraph) -> None:
        """Verifies cycle safety and node resolutions in the graph.

        Args:
            graph: The ObjectiveGraph to check.

        Raises:
            ValueError: If a cycle is detected or nodes are missing.
        """
        if not graph.nodes:
            raise ValueError("ObjectiveGraph must contain at least one node.")
        if graph.root_id not in graph.nodes:
            raise ValueError(f"Root node '{graph.root_id}' not found in ObjectiveGraph.")

        # Cycle detection using DFS (visited state map: 0 = unvisited, 1 = visiting, 2 = visited)
        visited: dict[str, int] = {node_id: 0 for node_id in graph.nodes}

        def dfs(curr_id: str) -> None:
            visited[curr_id] = 1  # visiting
            node = graph.nodes[curr_id]
            for dep_id in node.dependencies:
                if dep_id not in graph.nodes:
                    self._logger.error(
                        "Broken graph reference detected",
                        extra={"node_id": curr_id, "missing_dep": dep_id},
                    )
                    raise ValueError(f"Dependency '{dep_id}' of node '{curr_id}' not found in graph.")
                if visited[dep_id] == 1:
                    self._logger.error(
                        "Circular dependency detected in graph",
                        extra={"node_id": curr_id, "cyclic_dep": dep_id},
                    )
                    raise ValueError(f"Circular dependency detected in ObjectiveGraph involving: {curr_id} -> {dep_id}")
                if visited[dep_id] == 0:
                    dfs(dep_id)
            visited[curr_id] = 2  # visited

        for node_id in graph.nodes:
            if visited[node_id] == 0:
                dfs(node_id)

        self._logger.debug("ObjectiveGraph validation passed successfully")
