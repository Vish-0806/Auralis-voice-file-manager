"""Comprehensive Unit Tests for Phase 10.6: Multi-Step Planning Engine.

Validates:
- GoalAnalyzer: Rule-based request normalization, capability matching, and constraint extraction
- PlanGenerator: Template-driven generation of step-numbered Plan models with dependencies
- PlanValidator: Validation of empty plans, duplicate IDs, missing dependencies, graph cycles, and missing tools
- ExecutionPlanner: Topological dependency sorting for strict sequential execution order
- ExecutionMonitor: Lifecycle tracking across PENDING, RUNNING, COMPLETED, FAILED, SKIPPED states
- AIPlanner: End-to-end planner pipeline coordination
"""

# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict

from brain.ai import (
    AIPlanner,
    DefaultExecutionMonitor,
    DefaultExecutionPlanner,
    DefaultGoalAnalyzer,
    DefaultPlanGenerator,
    DefaultPlanValidator,
    DefaultToolRegistry,
    ExecutionPlanningError,
    GoalAnalysisError,
    Plan,
    PlanGenerationError,
    PlanningGoal,
    PlanStatus,
    PlanStep,
    PlanValidationError,
    StepDependency,
    StepStatus,
)


# ---------------------------------------------------------------------------
# Tests: GoalAnalyzer
# ---------------------------------------------------------------------------


def test_goal_analyzer_normalization_and_capability_extraction():
    """Test DefaultGoalAnalyzer normalizes text and extracts capabilities and constraints."""
    analyzer = DefaultGoalAnalyzer()

    goal = analyzer.analyze_goal("Please organize my documents folder carefully dry_run")

    assert isinstance(goal, PlanningGoal)
    assert goal.normalized_goal == "Please organize my documents folder carefully dry_run"
    assert "filesystem" in goal.required_capabilities
    assert goal.constraints.get("read_only") is True
    assert goal.constraints.get("safety_strict") is True


def test_goal_analyzer_empty_request_error():
    """Test GoalAnalyzer raises GoalAnalysisError for empty input."""
    analyzer = DefaultGoalAnalyzer()

    with pytest.raises(GoalAnalysisError):
        analyzer.analyze_goal("   ")


# ---------------------------------------------------------------------------
# Tests: PlanGenerator
# ---------------------------------------------------------------------------


def test_plan_generator_file_organization_plan():
    """Test DefaultPlanGenerator generates ordered plan with step dependencies."""
    analyzer = DefaultGoalAnalyzer()
    generator = DefaultPlanGenerator()

    goal = analyzer.analyze_goal("Organize files in /downloads dry_run")
    plan = generator.generate_plan(goal)

    assert isinstance(plan, Plan)
    assert len(plan.steps) == 2
    assert plan.steps[0].step_id == "step-1-scan"
    assert plan.steps[1].step_id == "step-2-organize"
    assert len(plan.steps[1].dependencies) == 1
    assert plan.steps[1].dependencies[0].depends_on_step_id == "step-1-scan"


# ---------------------------------------------------------------------------
# Tests: PlanValidator
# ---------------------------------------------------------------------------


def test_plan_validator_valid_plan():
    """Test DefaultPlanValidator validates clean plan without errors."""
    generator = DefaultPlanGenerator()
    validator = DefaultPlanValidator()
    goal = PlanningGoal(goal_id="g1", raw_text="Test", normalized_goal="Test")

    plan = generator.generate_plan(goal)
    res = validator.validate_plan(plan)

    assert res["is_valid"] is True
    assert res["errors"] == []


def test_plan_validator_empty_plan_error():
    """Test PlanValidator flags empty plans."""
    validator = DefaultPlanValidator()
    empty_plan = Plan(plan_id="p-empty", goal_id="g1", steps=[])

    res = validator.validate_plan(empty_plan)
    assert res["is_valid"] is False
    assert any("zero steps" in err for err in res["errors"])


def test_plan_validator_duplicate_step_id_error():
    """Test PlanValidator flags duplicate step IDs."""
    validator = DefaultPlanValidator()
    step1 = PlanStep(step_id="step-dup", step_number=1, description="Step 1", required_tool_name="tool_a")
    step2 = PlanStep(step_id="step-dup", step_number=2, description="Step 2", required_tool_name="tool_b")

    plan = Plan(plan_id="p-dup", goal_id="g1", steps=[step1, step2])
    res = validator.validate_plan(plan)

    assert res["is_valid"] is False
    assert any("Duplicate step ID" in err for err in res["errors"])


def test_plan_validator_missing_dependency_error():
    """Test PlanValidator flags dependencies pointing to non-existent step IDs."""
    validator = DefaultPlanValidator()
    dep = StepDependency(step_id="step-2", depends_on_step_id="non-existent-step")
    step1 = PlanStep(step_id="step-1", step_number=1, description="Step 1", required_tool_name="tool_a")
    step2 = PlanStep(step_id="step-2", step_number=2, description="Step 2", required_tool_name="tool_b", dependencies=[dep])

    plan = Plan(plan_id="p-missing-dep", goal_id="g1", steps=[step1, step2])
    res = validator.validate_plan(plan)

    assert res["is_valid"] is False
    assert any("missing step" in err for err in res["errors"])


def test_plan_validator_cyclic_dependency_error():
    """Test PlanValidator detects graph cycles in step dependencies."""
    validator = DefaultPlanValidator()

    dep1 = StepDependency(step_id="step-1", depends_on_step_id="step-2")
    dep2 = StepDependency(step_id="step-2", depends_on_step_id="step-1")

    step1 = PlanStep(step_id="step-1", step_number=1, description="Step 1", required_tool_name="tool_a", dependencies=[dep1])
    step2 = PlanStep(step_id="step-2", step_number=2, description="Step 2", required_tool_name="tool_b", dependencies=[dep2])

    plan = Plan(plan_id="p-cycle", goal_id="g1", steps=[step1, step2])
    res = validator.validate_plan(plan)

    assert res["is_valid"] is False
    assert any("Cyclic dependency" in err for err in res["errors"])


def test_plan_validator_unregistered_tool_warning():
    """Test PlanValidator flags unregistered tool names as warnings."""
    validator = DefaultPlanValidator()
    registry = DefaultToolRegistry()  # Empty registry

    step = PlanStep(step_id="step-1", step_number=1, description="Step 1", required_tool_name="unregistered_tool")
    plan = Plan(plan_id="p-unreg", goal_id="g1", steps=[step])

    res = validator.validate_plan(plan, tool_registry=registry)
    assert res["is_valid"] is True
    assert len(res["warnings"]) == 1
    assert "not registered" in res["warnings"][0]


# ---------------------------------------------------------------------------
# Tests: ExecutionPlanner
# ---------------------------------------------------------------------------


def test_execution_planner_topological_sorting():
    """Test DefaultExecutionPlanner resolves topological sequential step order."""
    planner = DefaultExecutionPlanner()

    step1 = PlanStep(step_id="step-scan", step_number=1, description="Scan", required_tool_name="scan_dir")
    dep = StepDependency(step_id="step-clean", depends_on_step_id="step-scan")
    step2 = PlanStep(step_id="step-clean", step_number=2, description="Clean", required_tool_name="clean_dir", dependencies=[dep])

    plan = Plan(plan_id="p-seq", goal_id="g1", steps=[step2, step1])  # Out of order input list

    ordered = planner.determine_execution_order(plan)
    assert len(ordered) == 2
    assert ordered[0].step_id == "step-scan"
    assert ordered[1].step_id == "step-clean"


# ---------------------------------------------------------------------------
# Tests: ExecutionMonitor
# ---------------------------------------------------------------------------


def test_execution_monitor_lifecycle():
    """Test DefaultExecutionMonitor records step lifecycle transitions and duration."""
    monitor = DefaultExecutionMonitor()

    monitor.track_step_start("step-1")
    res1 = monitor.track_step_complete("step-1", output={"status": "ok"}, duration_ms=12.5)

    res2 = monitor.track_step_fail("step-2", error_message="File not found", duration_ms=5.0)
    res3 = monitor.track_step_skip("step-3", reason="Upstream failed")

    assert res1.status == StepStatus.COMPLETED
    assert res1.execution_time_ms == 12.5
    assert res2.status == StepStatus.FAILED
    assert res3.status == StepStatus.SKIPPED

    summary = monitor.get_execution_summary()
    assert summary["total_steps_tracked"] == 3
    assert summary["completed_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["skipped_count"] == 1


# ---------------------------------------------------------------------------
# Tests: AIPlanner End-to-End Coordination
# ---------------------------------------------------------------------------


def test_ai_planner_end_to_end_orchestration():
    """Test high-level AIPlanner service executes full goal -> plan -> validate pipeline."""
    planner = AIPlanner()

    res = planner.create_and_validate_plan("Organize project files in /workspace dry_run")

    assert res["is_valid"] is True
    assert isinstance(res["goal"], PlanningGoal)
    assert isinstance(res["plan"], Plan)
    assert res["plan"].status == PlanStatus.VALIDATED
    assert len(res["ordered_steps"]) == 2
