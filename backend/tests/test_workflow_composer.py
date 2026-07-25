"""Unit tests for the Workflow Composer subsystem in Auralis."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from core.intents import Intent
from automation.workflow.models import WorkflowStep, WorkflowDefinition
from brain.planning.models import ExecutionStep
from brain.planning.workflow_composer import (
    WorkflowComposer,
    WorkflowComposition,
    WorkflowCompositionResult,
    WorkflowMergeConflict,
)
from brain.planning.task_planner import TaskPlanner


def test_workflow_composer_success_merge():
    """Checks that WorkflowComposer successfully merges compatible workflows and steps."""
    composer = WorkflowComposer()

    # Matched workflow: Start Coding
    wf = WorkflowDefinition(
        name="Start Coding",
        description="Launch dev tools",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="VS Code"),
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="Terminal"),
        ],
    )

    # Dynamic step: Set volume to 30
    step_vol = ExecutionStep(
        step_id="step_set_volume",
        intent=Intent.SET_VOLUME,
        target="30",
    )

    comp = WorkflowComposition(
        name="Composed Coding Routine",
        description="Coding routine with volume prep",
        workflows=[wf],
        steps=[step_vol],
    )

    result = composer.compose(comp)

    assert len(result.conflicts) == 0
    assert result.merged_workflow is not None
    assert result.merged_workflow.name == "Composed Coding Routine"
    assert len(result.merged_workflow.steps) == 3
    intents = [s.intent for s in result.merged_workflow.steps]
    assert intents.count(Intent.OPEN_APPLICATION) == 2
    assert intents.count(Intent.SET_VOLUME) == 1
    assert "Start Coding" in result.reused_workflows
    assert "Composed Coding Routine" in result.generated_workflows


def test_workflow_composer_parameter_conflict():
    """Checks that WorkflowComposer detects conflicting targets for single-value/exclusive intents."""
    composer = WorkflowComposer()

    # Step 1: Set volume to 30
    step_30 = ExecutionStep(
        step_id="volume_low",
        intent=Intent.SET_VOLUME,
        target="30",
    )
    # Step 2: Set volume to 80
    step_80 = ExecutionStep(
        step_id="volume_high",
        intent=Intent.SET_VOLUME,
        target="80",
    )

    comp = WorkflowComposition(
        name="Conflict Route",
        description="",
        workflows=[],
        steps=[step_30, step_80],
    )

    result = composer.compose(comp)

    assert len(result.conflicts) == 1
    assert result.conflicts[0].conflict_type == "conflicting_parameters"
    assert result.conflicts[0].step_id == "SET_VOLUME"
    assert "Conflicting target volumes" in result.conflicts[0].message


def test_workflow_composer_exclusive_action_conflict():
    """Checks that WorkflowComposer blocks exclusive actions combined with interactive steps."""
    composer = WorkflowComposer()

    # Lock PC step
    step_lock = ExecutionStep(
        step_id="step_lock_pc",
        intent=Intent.LOCK_PC,
    )
    # Open app step
    step_open = ExecutionStep(
        step_id="step_open_app",
        intent=Intent.OPEN_APPLICATION,
        target="VS Code",
    )

    comp = WorkflowComposition(
        name="Conflict Route",
        description="",
        workflows=[],
        steps=[step_lock, step_open],
    )

    result = composer.compose(comp)

    assert len(result.conflicts) == 1
    assert result.conflicts[0].conflict_type == "exclusive_action"
    assert result.conflicts[0].step_id == "LOCK_PC"
    assert "Cannot perform open application" in result.conflicts[0].message


def test_workflow_composer_ordering_conflict():
    """Checks that WorkflowComposer detects circular ordering dependencies."""
    composer = WorkflowComposer()

    # Matched workflow 1: A -> B
    wf1 = WorkflowDefinition(
        name="W1",
        description="",
        steps=[
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="A"),
            WorkflowStep(intent=Intent.OPEN_APPLICATION, target="B"),
        ],
    )
    # Since we can't easily model custom dependency overrides crossing between library workflows
    # directly using simple steps without unique IDs, the composer assigns:
    # wf_0_step_0_open_application (A) -> wf_0_step_1_open_application (B).
    # If we add custom steps that explicitly require B to run before A:
    # But wait, in the composer, we add implicit sequencing dependencies between steps of a workflow.
    # To cause a cycle across workflows, we would need dependencies crossing between them.
    # Let's check how ordering/cycle is detected: if we have a cycle in the ExecutionSequence resolver.
    # We can write a custom test for composer cycle checking by manually crafting steps with cyclic dependencies
    # if the resolver cycle check throws.
    # Let's see: we can mock or inject a dependency cycle in a custom resolver, or let's create a cycle by merging
    # steps where one step has explicit dependency matching a cycle.
    # For example, if we have dynamic steps step_1 (depends on step_2) and step_2 (depends on step_1),
    # that is a direct cyclic dependency!
    # Let's test that:
    from brain.planning.models import ExecutionDependency
    # In WorkflowComposition, composition.steps holds ExecutionStep objects.
    # ExecutionStep itself does not hold dependency edges. Dependencies are resolved from implicit workflow order.
    # Wait, does composition contain dependency lists? No, it has steps and workflows.
    # If we have two workflows that share the same step IDs, or if the resolver encounters a cycle from implicit order?
    # Wait! Can we cause a cycle by creating two workflows that reference each other, or duplicate step IDs?
    # Yes, if the step IDs collide.
    # But the composer constructs unique step IDs for workflow steps: f"wf_{wf_idx}_step_{step_idx}_{intent}"
    # Wait! How can there be an ordering cycle then?
    # If the user or planning logic supplies duplicate dynamic steps that contain explicit cycles?
    # Wait, the `TaskPlanner` uses `DependencyBuilder` to build dependencies.
    # Let's mock the `DependencyResolver.resolve_order` to raise a `ValueError` (simulating cycle failure)
    # to verify that the composer translates it correctly to a WorkflowMergeConflict of type "ordering"!
    # This is a very clean and reliable unit test.
    
    from unittest.mock import MagicMock
    from brain.planning.dependency_resolver import DependencyResolver
    mock_resolver = MagicMock(spec=DependencyResolver)
    mock_resolver.resolve_order.side_effect = ValueError("Cycle detected: A -> B -> A")

    composer_mocked = WorkflowComposer(dependency_resolver=mock_resolver)
    
    comp = WorkflowComposition(
        name="Cycle Route",
        description="",
        workflows=[],
        steps=[ExecutionStep(step_id="step_a", intent=Intent.MUTE)],
    )
    
    result = composer_mocked.compose(comp)
    assert len(result.conflicts) == 1
    assert result.conflicts[0].conflict_type == "ordering"
    assert result.conflicts[0].step_id == "sequence_cycle"
    assert "Circular dependency cycle detected" in result.conflicts[0].message


def test_task_planner_composer_injection():
    """Checks that TaskPlanner constructor accepts workflow composer inject."""
    composer = WorkflowComposer()
    planner = TaskPlanner(workflow_composer=composer)
    assert planner._workflow_composer is composer
