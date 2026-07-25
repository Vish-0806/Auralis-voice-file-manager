"""Plan optimizer removing duplicates and optimizing step scheduling in Auralis."""

from __future__ import annotations

import logging
from typing import Any, List, Dict, Optional, Set
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from .models import ExecutionStep, ExecutionDependency
from .workflow_composer import WorkflowCompositionResult


class OptimizationRule(BaseModel):
    """Represents a rule applied during plan optimization."""

    name: str = Field(description="Name of the optimization rule")
    description: str = Field(description="Summary of what the rule accomplishes")


class OptimizationReport(BaseModel):
    """Represents the rich details of optimization modifications."""

    removed_steps: List[str] = Field(
        default_factory=list, description="IDs of steps removed during optimization"
    )
    merged_steps: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of child step ID -> parent step ID indicating merged steps"
    )
    parallel_groups: List[List[str]] = Field(
        default_factory=list, description="Groups of step IDs that can execute in parallel"
    )
    estimated_execution_reduction: float = Field(
        0.0, description="Percentage of execution time reduction estimated (e.g. 0.33)"
    )
    applied_rules: List[str] = Field(
        default_factory=list, description="Names of the optimization rules applied"
    )


class OptimizationResult(BaseModel):
    """Represents the output of plan optimization."""

    steps: List[ExecutionStep] = Field(default_factory=list, description="Optimized list of ExecutionSteps")
    report: OptimizationReport = Field(description="Summary report of optimizations made")


class PlanOptimizer:
    """Optimizes execution steps by removing duplicates and flagging parallel paths."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the PlanOptimizer.

        Args:
            logger: Optional custom logger for optimization diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def optimize_plan(
        self,
        steps: list[ExecutionStep],
        dependencies: list[ExecutionDependency] | None = None,
        workflow_composition_result: WorkflowCompositionResult | None = None,
    ) -> list[ExecutionStep] | OptimizationResult:
        """Deduplicates and optimizes the execution sequence.

        Supports both modern OptimizationResult return types and legacy step list fallbacks
        to maintain backward compatibility.

        Args:
            steps: The list of ordered execution steps.
            dependencies: List of dependency edges between steps.
            workflow_composition_result: Optional composition results to check.

        Returns:
            OptimizationResult or list of optimized ExecutionSteps.
        """
        self._logger.info("Optimizing execution plan steps", extra={"input_steps_count": len(steps)})

        # Detect legacy invocation
        is_legacy = dependencies is None

        # 1. Apply Deduplication Rule & Redundant Preparation Elimination
        deduplicated_steps: list[ExecutionStep] = []
        seen_keys: set[tuple[str, str | None]] = set()
        removed_steps: list[str] = []
        applied_rules: list[str] = []

        for step in steps:
            key = (step.intent.value, step.target)
            if key in seen_keys:
                self._logger.info(
                    "Removing duplicate step during optimization",
                    extra={"step_id": step.step_id, "intent": step.intent.value, "target": step.target},
                )
                removed_steps.append(step.step_id)
                continue
            
            # Specific rule: Eliminate redundant ENABLE_WIFI prep steps
            if step.intent.value == "ENABLE_WIFI" and any(s.intent.value == "ENABLE_WIFI" for s in deduplicated_steps):
                self._logger.info(
                    "Removing redundant WiFi prep step",
                    extra={"step_id": step.step_id},
                )
                removed_steps.append(step.step_id)
                continue

            seen_keys.add(key)
            deduplicated_steps.append(step.model_copy(deep=True))

        if removed_steps:
            applied_rules.append("Deduplication")
            applied_rules.append("Redundant Preparation Elimination")

        # 2. Build Dependency graph depth level to group parallelizable independent steps
        parallel_groups: list[list[str]] = []
        deps = dependencies or []
        
        # Build adjacency list: node -> set of parents it depends on
        adj_in: dict[str, set[str]] = {s.step_id: set() for s in deduplicated_steps}
        for d in deps:
            if d.step_id in adj_in:
                adj_in[d.step_id].update(d.depends_on)

        # Calculate depths recursively with memoization
        depths: dict[str, int] = {}
        def get_depth(s_id: str) -> int:
            if s_id in depths:
                return depths[s_id]
            parents = adj_in.get(s_id, set())
            if not parents:
                depths[s_id] = 0
                return 0
            max_p_depth = 0
            for p in parents:
                if p in adj_in:
                    max_p_depth = max(max_p_depth, get_depth(p))
            depths[s_id] = max_p_depth + 1
            return depths[s_id]

        for s in deduplicated_steps:
            get_depth(s.step_id)

        # Group steps by depth
        levels: dict[int, list[ExecutionStep]] = {}
        for s in deduplicated_steps:
            d = depths.get(s.step_id, 0)
            levels.setdefault(d, []).append(s)

        # Group parallelizable steps at each depth level
        optimized_steps: list[ExecutionStep] = []
        for level_idx, level_steps in sorted(levels.items()):
            parallel_candidates = [s for s in level_steps if s.can_parallel]
            
            # If multiple parallel candidates exist, flag them as group
            if len(parallel_candidates) > 1:
                group_ids = [s.step_id for s in parallel_candidates]
                parallel_groups.append(group_ids)
                
                for s in level_steps:
                    updated_params = s.parameters.copy()
                    if s.can_parallel:
                        updated_params["opt_parallel_group"] = level_idx + 1
                    else:
                        updated_params["opt_parallel_group"] = 0
                    
                    optimized_steps.append(
                        ExecutionStep(
                            step_id=s.step_id,
                            intent=s.intent,
                            target=s.target,
                            parameters=updated_params,
                            can_parallel=s.can_parallel,
                        )
                    )
            else:
                for s in level_steps:
                    updated_params = s.parameters.copy()
                    if s.can_parallel:
                        updated_params["opt_parallel_group"] = 1
                    else:
                        updated_params["opt_parallel_group"] = 0
                        
                    optimized_steps.append(
                        ExecutionStep(
                            step_id=s.step_id,
                            intent=s.intent,
                            target=s.target,
                            parameters=updated_params,
                            can_parallel=s.can_parallel,
                        )
                    )

        if parallel_groups:
            applied_rules.append("Parallel Grouping")

        # 3. Calculate estimated execution reduction percentage
        estimated_execution_reduction = 0.0
        seq_count = len(steps)
        if seq_count > 0:
            saved_time = sum(len(g) - 1 for g in parallel_groups)
            estimated_execution_reduction = round(saved_time / seq_count, 4)

        # 4. If composition result passed, tag it
        if workflow_composition_result:
            applied_rules.append("Workflow Integration")

        report = OptimizationReport(
            removed_steps=removed_steps,
            merged_steps={},
            parallel_groups=parallel_groups,
            estimated_execution_reduction=estimated_execution_reduction,
            applied_rules=applied_rules,
        )

        self._logger.info(
            "Optimization report generated successfully",
            extra={"reduction_ratio": estimated_execution_reduction, "applied_rules_count": len(applied_rules)},
        )

        if is_legacy:
            return optimized_steps

        return OptimizationResult(steps=optimized_steps, report=report)
