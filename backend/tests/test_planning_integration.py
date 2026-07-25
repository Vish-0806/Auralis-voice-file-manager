"""Integration tests for the Auralis Planning Engine subsystems."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from core.intents import Intent
from core.models import ExecutionPlan as CoreExecutionPlan
from brain.reasoning.models import Objective, Constraint, Priority, ReasoningResult
from brain.planning.models import ExecutionStep
from brain.planning.objective_graph import ObjectiveGraph
from brain.planning.goal_decomposer import GoalDecomposer
from brain.planning.objective_analyzer import ObjectiveAnalyzer
from brain.planning.subtask_generator import SubtaskGenerator
from brain.planning.dependency_builder import DependencyBuilder
from brain.planning.dependency_resolver import DependencyResolver
from brain.planning.plan_optimizer import PlanOptimizer, OptimizationResult
from brain.planning.workflow_library import WorkflowLibrary, WorkflowMetadata
from brain.planning.workflow_matcher import WorkflowMatcher, WorkflowMatchQuery
from brain.planning.workflow_composer import WorkflowComposer, WorkflowComposition
from brain.planning.workflow_compiler import WorkflowCompiler
from brain.planning.task_planner import TaskPlanner


def test_end_to_end_planning_pipeline():
    """Verifies that all planning components participate correctly in the TaskPlanner pipeline."""
    # 1. Instantiate the planning stack
    decomposer = GoalDecomposer()
    analyzer = ObjectiveAnalyzer()
    generator = SubtaskGenerator()
    dep_builder = DependencyBuilder()
    resolver = DependencyResolver()
    library = WorkflowLibrary()
    matcher = WorkflowMatcher()
    composer = WorkflowComposer(dependency_resolver=resolver)
    optimizer = PlanOptimizer()
    compiler = WorkflowCompiler()

    planner = TaskPlanner(
        goal_decomposer=decomposer,
        objective_analyzer=analyzer,
        subtask_generator=generator,
        dependency_builder=dep_builder,
        dependency_resolver=resolver,
        workflow_library=library,
        workflow_matcher=matcher,
        workflow_composer=composer,
        plan_optimizer=optimizer,
        workflow_compiler=compiler,
    )

    # 2. Formulate a ReasoningResult with internet constraint unsatisfied
    c_internet = Constraint(name="Internet Connection", type="internet", description="", satisfied=False)
    res = ReasoningResult(
        goal_name="START_CODING",
        objective=Objective(title="Coding Workspace Setup", description="Start code tools"),
        required_capabilities=["desktop", "workflow"],
        constraints=[c_internet],
        priority=Priority.MEDIUM,
        estimated_complexity="MEDIUM",
    )

    # 3. Trigger planner
    plan = planner.plan(res)

    # 4. Verify compiler output
    assert isinstance(plan, CoreExecutionPlan)
    assert plan.intent == Intent.RUN_WORKFLOW
    assert "Start Coding" in plan.target  # compiled dynamically from target name

    # 5. Check library registration consistency
    compiled_wf = library.get_workflow(plan.target)
    assert compiled_wf is not None
    assert len(compiled_wf.steps) == 4  # 1 prep (WiFi) + 3 coding steps
    assert compiled_wf.steps[0].intent == Intent.ENABLE_WIFI


def test_workflow_composition_and_parallel_optimization_integration():
    """Verifies matching, composition, and optimization of library workflows with dynamic steps."""
    library = WorkflowLibrary()
    matcher = WorkflowMatcher()
    composer = WorkflowComposer()
    optimizer = PlanOptimizer()

    # 1. Query for "Study Mode"
    query = WorkflowMatchQuery(goal_name="STUDY")
    matches = matcher.match(library, query)
    
    assert len(matches) > 0
    study_wf = matches[0].workflow

    # 2. Dynamic step: Set volume to 30 (can run in parallel with mute/browser)
    step_vol = ExecutionStep(
        step_id="step_set_volume",
        intent=Intent.SET_VOLUME,
        target="30",
        can_parallel=True,
    )

    # 3. Compose them
    comp = WorkflowComposition(
        name="Study with Volume Adjust",
        description="Focused study mode with custom volume",
        workflows=[study_wf],
        steps=[step_vol],
    )
    comp_result = composer.compose(comp)

    assert len(comp_result.conflicts) == 0
    composed_wf = comp_result.merged_workflow
    assert composed_wf is not None

    # 4. Run through PlanOptimizer with dependency structure
    # Since composed steps are converted from WorkflowSteps, we map them back to ExecutionSteps
    opt_steps = [
        ExecutionStep(
            step_id=f"step_{idx}",
            intent=s.intent,
            target=s.target,
            can_parallel=(s.intent in {Intent.SET_VOLUME, Intent.MUTE}),
        )
        for idx, s in enumerate(composed_wf.steps)
    ]

    opt_result = optimizer.optimize_plan(opt_steps, dependencies=[])
    assert isinstance(opt_result, OptimizationResult)
    
    # Assert parallel group formed for independent mute + volume steps
    assert len(opt_result.report.parallel_groups) > 0
    applied_rules = opt_result.report.applied_rules
    assert "Parallel Grouping" in applied_rules
