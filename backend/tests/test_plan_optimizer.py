"""Unit tests for the Plan Optimizer subsystem in Auralis."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from core.intents import Intent
from brain.planning.models import ExecutionStep, ExecutionDependency
from brain.planning.plan_optimizer import PlanOptimizer, OptimizationResult


def test_plan_optimizer_deduplication():
    """Checks that PlanOptimizer removes duplicate steps and records them in the report."""
    optimizer = PlanOptimizer()

    steps = [
        ExecutionStep(step_id="step_1", intent=Intent.OPEN_APPLICATION, target="VS Code"),
        ExecutionStep(step_id="step_2", intent=Intent.OPEN_APPLICATION, target="VS Code"),  # Duplicate
        ExecutionStep(step_id="step_3", intent=Intent.MUTE),
    ]

    result = optimizer.optimize_plan(steps, dependencies=[])
    
    assert isinstance(result, OptimizationResult)
    assert len(result.steps) == 2
    assert result.steps[0].step_id == "step_1"
    assert result.steps[1].step_id == "step_3"
    
    assert "step_2" in result.report.removed_steps
    assert "Deduplication" in result.report.applied_rules


def test_plan_optimizer_redundant_prep_elimination():
    """Checks that PlanOptimizer eliminates redundant prep steps of the same intent."""
    optimizer = PlanOptimizer()

    steps = [
        ExecutionStep(step_id="prep_wifi_1", intent=Intent.ENABLE_WIFI),
        ExecutionStep(step_id="prep_wifi_2", intent=Intent.ENABLE_WIFI),  # Redundant
        ExecutionStep(step_id="step_launch", intent=Intent.OPEN_APPLICATION, target="Browser"),
    ]

    result = optimizer.optimize_plan(steps, dependencies=[])
    assert len(result.steps) == 2
    assert result.steps[0].step_id == "prep_wifi_1"
    assert "prep_wifi_2" in result.report.removed_steps
    assert "Redundant Preparation Elimination" in result.report.applied_rules


def test_plan_optimizer_parallel_grouping_and_reduction():
    """Checks that PlanOptimizer forms parallel groups by dependency level and computes reductions."""
    optimizer = PlanOptimizer()

    # Step 1: Open app (not parallelizable)
    # Step 2: launch terminal (can_parallel=True)
    # Step 3: set volume (can_parallel=True)
    # Step 2 and Step 3 depend on Step 1. They are at Depth Level 1 and can run in parallel.
    steps = [
        ExecutionStep(step_id="step_1", intent=Intent.OPEN_APPLICATION, target="VS Code", can_parallel=False),
        ExecutionStep(step_id="step_2", intent=Intent.OPEN_APPLICATION, target="Terminal", can_parallel=True),
        ExecutionStep(step_id="step_3", intent=Intent.SET_VOLUME, target="30", can_parallel=True),
    ]

    dependencies = [
        ExecutionDependency(step_id="step_2", depends_on=["step_1"]),
        ExecutionDependency(step_id="step_3", depends_on=["step_1"]),
    ]

    result = optimizer.optimize_plan(steps, dependencies=dependencies)
    
    assert len(result.steps) == 3
    # Check parallel groups: step_2 and step_3 should be grouped
    assert len(result.report.parallel_groups) == 1
    group = result.report.parallel_groups[0]
    assert "step_2" in group
    assert "step_3" in group

    # Estimated reduction calculation:
    # 3 total steps. Saved time = (2 - 1) = 1.
    # Reduction = 1 / 3 = 0.3333
    assert result.report.estimated_execution_reduction == 0.3333
    assert "Parallel Grouping" in result.report.applied_rules

    # Check opt_parallel_group parameter mapping: Level 1 + 1 = 2
    assert result.steps[1].parameters.get("opt_parallel_group") == 2
    assert result.steps[2].parameters.get("opt_parallel_group") == 2


def test_plan_optimizer_legacy_compatibility():
    """Checks that PlanOptimizer supports legacy list inputs and returns simple lists."""
    optimizer = PlanOptimizer()

    steps = [
        ExecutionStep(step_id="step_1", intent=Intent.OPEN_APPLICATION, target="VS Code"),
        ExecutionStep(step_id="step_2", intent=Intent.OPEN_APPLICATION, target="VS Code"),
    ]

    # Call without dependencies (legacy signature)
    result = optimizer.optimize_plan(steps)
    
    # Must return a simple list directly
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].step_id == "step_1"
