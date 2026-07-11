"""Unit tests for the Auralis Dynamic Task Planner subsystem and core Planner integration."""

from __future__ import annotations

import os
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock
# pyrefly: ignore [missing-import]
import pytest

from core.models import AssistantRequest
from core.intents import Intent
from core.planner import Planner
from brain.goal.models import Goal, GoalCategory
from brain.reasoning.models import Objective, Constraint, Priority, ReasoningResult
from brain.planning.models import ExecutionStep, ExecutionDependency, ExecutionSequence
from brain.planning.plan_builder import PlanBuilder
from brain.planning.dependency_resolver import DependencyResolver
from brain.planning.plan_optimizer import PlanOptimizer
from brain.planning.task_planner import TaskPlanner
from automation.workflow.workflow_registry import WorkflowRegistry


# --- Models Validation Tests ---

def test_planning_models_validation():
    """Validates that ExecutionStep, ExecutionDependency, and ExecutionSequence can be instantiated."""
    step1 = ExecutionStep(step_id="1", intent=Intent.MUTE, target=None)
    step2 = ExecutionStep(step_id="2", intent=Intent.SET_VOLUME, target="50")
    dep = ExecutionDependency(step_id="2", depends_on=["1"])
    seq = ExecutionSequence(steps=[step1, step2], dependencies=[dep])

    assert len(seq.steps) == 2
    assert seq.dependencies[0].step_id == "2"
    assert seq.dependencies[0].depends_on == ["1"]


# --- Plan Builder Tests ---

def test_plan_builder_remediation_steps():
    """Validates that PlanBuilder injects remediation steps for unsatisfied constraints."""
    builder = PlanBuilder()
    
    # Satisfied internet constraint
    c_satisfied = Constraint(name="Internet", type="internet", description="", satisfied=True)
    res_sat = ReasoningResult(
        goal_name="MEETING",
        objective=Objective(title="", description=""),
        required_capabilities=["desktop"],
        constraints=[c_satisfied],
        priority=Priority.HIGH,
        estimated_complexity="MEDIUM"
    )
    seq_sat = builder.build_steps(res_sat)
    assert not any(s.intent == Intent.ENABLE_WIFI for s in seq_sat.steps)

    # Unsatisfied internet constraint
    c_unsatisfied = Constraint(name="Internet", type="internet", description="", satisfied=False)
    res_unsat = ReasoningResult(
        goal_name="MEETING",
        objective=Objective(title="", description=""),
        required_capabilities=["desktop"],
        constraints=[c_unsatisfied],
        priority=Priority.HIGH,
        estimated_complexity="MEDIUM"
    )
    seq_unsat = builder.build_steps(res_unsat)
    assert any(s.intent == Intent.ENABLE_WIFI for s in seq_unsat.steps)
    
    # Check that main action steps depend on the prep step
    dep_show = next(d for d in seq_unsat.dependencies if d.step_id == "step_show_desktop")
    assert "prep_enable_wifi" in dep_show.depends_on


# --- Dependency Resolver Tests ---

def test_dependency_resolver_topological_sort():
    """Validates topological sorting and order enforcement."""
    resolver = DependencyResolver()
    
    step1 = ExecutionStep(step_id="A", intent=Intent.MUTE)
    step2 = ExecutionStep(step_id="B", intent=Intent.SHOW_DESKTOP)
    step3 = ExecutionStep(step_id="C", intent=Intent.LOCK_PC)

    # C depends on B, B depends on A
    dep1 = ExecutionDependency(step_id="C", depends_on=["B"])
    dep2 = ExecutionDependency(step_id="B", depends_on=["A"])
    
    seq = ExecutionSequence(steps=[step3, step2, step1], dependencies=[dep1, dep2])
    ordered = resolver.resolve_order(seq)
    
    # Verification: order must be A -> B -> C
    assert [s.step_id for s in ordered] == ["A", "B", "C"]


def test_dependency_resolver_circular_dependency():
    """Validates that DependencyResolver raises a ValueError on circular dependencies."""
    resolver = DependencyResolver()
    
    step1 = ExecutionStep(step_id="A", intent=Intent.MUTE)
    step2 = ExecutionStep(step_id="B", intent=Intent.LOCK_PC)

    # A depends on B, B depends on A
    dep1 = ExecutionDependency(step_id="A", depends_on=["B"])
    dep2 = ExecutionDependency(step_id="B", depends_on=["A"])
    
    seq = ExecutionSequence(steps=[step1, step2], dependencies=[dep1, dep2])
    with pytest.raises(ValueError) as excinfo:
        resolver.resolve_order(seq)
    assert "Circular dependency" in str(excinfo.value)


# --- Plan Optimizer Tests ---

def test_plan_optimizer_deduplication_and_parallel():
    """Validates deduplication of steps and parallel group configuration."""
    optimizer = PlanOptimizer()
    
    step1 = ExecutionStep(step_id="1", intent=Intent.MUTE)
    step2 = ExecutionStep(step_id="2", intent=Intent.MUTE)  # Duplicate
    step3 = ExecutionStep(step_id="3", intent=Intent.SET_VOLUME, target="30", can_parallel=True)

    optimized = optimizer.optimize_plan([step1, step2, step3])
    
    # Deduplication check: step2 (duplicate MUTE) should be removed
    assert len(optimized) == 2
    assert [s.step_id for s in optimized] == ["1", "3"]
    
    # Parallel check: step3 is marked can_parallel, should have group ID 1
    assert optimized[1].parameters["opt_parallel_group"] == 1


# --- Task Planner Integration Tests ---

def test_task_planner_single_step():
    """Validates that a single-step goal returns the intent directly."""
    planner = TaskPlanner()
    
    res = ReasoningResult(
        goal_name="LOCK_COMPUTER",
        objective=Objective(title="Lock PC", description="", target="PC"),
        required_capabilities=["desktop"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW"
    )
    
    plan = planner.plan(res)
    assert plan.intent == Intent.LOCK_PC
    assert plan.target is None


def test_task_planner_multi_step_workflow():
    """Validates that multi-step goals compile into a dynamic workflow and register it in the registry."""
    planner = TaskPlanner()
    
    res = ReasoningResult(
        goal_name="START_CODING",
        objective=Objective(title="Start Coding", description="", target="VS Code"),
        required_capabilities=["desktop", "workflow"],
        constraints=[],
        priority=Priority.MEDIUM,
        estimated_complexity="MEDIUM"
    )
    
    plan = planner.plan(res)
    assert plan.intent == Intent.RUN_WORKFLOW
    assert plan.target == "Start Coding"
    
    # Verify the workflow was registered dynamically
    registered_wf = WorkflowRegistry._dynamic_registry.get(plan.target)
    assert registered_wf is not None
    assert len(registered_wf.steps) == 3
    assert registered_wf.steps[0].intent == Intent.OPEN_APPLICATION
    assert registered_wf.steps[0].target == "VS Code"


# --- Core Planner Integration Test ---

def test_core_planner_dynamic_task_planning():
    """Validates full pipeline: request -> interpreter -> reasoning -> task planner -> workflow registration."""
    planner = Planner()
    
    req = AssistantRequest(
        message="lock pc",
        source="test",
        timestamp=datetime.now(UTC)
    )
    
    plan = planner.create_plan(req)
    # Verification: Should run TaskPlanner, return LOCK_PC, and embed reasoning metadata
    assert plan.intent == Intent.LOCK_PC
    assert "reasoning" in plan.parameters
    assert plan.parameters["reasoning"]["priority"] == "CRITICAL"
