"""Routine Optimizer cleaning up redundancies and estimating runtimes."""

import logging
from typing import Any, Dict, List, Tuple
from memory.routines.models import RoutineOptimisationReport

logger = logging.getLogger(__name__)


class RoutineOptimizer:
    """Optimizes routine action steps by removing redundancies and grouping calls."""

    def optimize_sequence(self, steps: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], RoutineOptimisationReport]:
        """Trims execution sequences, simplifies parameters, and estimates savings."""
        original_count = len(steps)
        optimised: List[Dict[str, Any]] = []
        applied_rules: List[str] = []

        seen_actions = set()
        for step in steps:
            # Copy step to prevent side effects
            step_copy = dict(step)
            action = step_copy.get("action") or step_copy.get("intent")

            # 1. Duplicate removal check
            if action in seen_actions:
                applied_rules.append(f"Removed duplicate action: {action}")
                continue

            seen_actions.add(action)

            # 2. Dependency / Parameter simplification (pruning default empty params)
            params = step_copy.get("parameters", {})
            if isinstance(params, dict):
                cleaned_params = {k: v for k, v in params.items() if v is not None and v != ""}
                step_copy["parameters"] = cleaned_params

            # 3. Execution grouping (tagging steps that can execute in parallel)
            # Standard independent steps get grouped together
            step_copy["execution_group"] = 1
            optimised.append(step_copy)

        # Estimate savings (assume average 200ms per step execution overhead)
        reduction_ms = (original_count - len(optimised)) * 200.0

        report = RoutineOptimisationReport(
            original_steps_count=original_count,
            optimised_steps_count=len(optimised),
            optimisations_applied=applied_rules,
            estimated_runtime_reduction_ms=reduction_ms
        )

        logger.info(f"Routine optimized: {original_count} -> {len(optimised)} steps (saved {reduction_ms}ms)")
        return optimised, report
