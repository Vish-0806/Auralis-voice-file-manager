"""Unit tests for the Workflow Matcher subsystem in Auralis."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from core.intents import Intent
from automation.workflow.models import WorkflowStep, WorkflowDefinition
from brain.reasoning.models import Objective, Constraint, Priority, ReasoningResult
from brain.planning.objective_graph import ObjectiveNode, ObjectiveGraph
from brain.planning.workflow_library import WorkflowLibrary, WorkflowMetadata, WorkflowSignature
from brain.planning.workflow_matcher import WorkflowMatcher, WorkflowMatchQuery
from brain.planning.task_planner import TaskPlanner


def test_workflow_matcher_priority_scoring():
    """Checks that the WorkflowMatcher prioritizes and weights matching parameters correctly."""
    lib = WorkflowLibrary()
    matcher = WorkflowMatcher()

    # Query with exact goal name (START_CODING maps to "Start Coding")
    query = WorkflowMatchQuery(goal_name="START_CODING")
    matches = matcher.match(lib, query)
    
    assert len(matches) > 0
    # The top match should be "Start Coding" with 1.0 confidence
    assert matches[0].workflow.name == "Start Coding"
    assert matches[0].confidence == 1.0
    assert "goal_name" in matches[0].matched_fields
    assert matches[0].score_breakdown["goal_name_score"] == 1.0

    # Query with exact workflow name
    query_name = WorkflowMatchQuery(workflow_name="Study Mode")
    matches_name = matcher.match(lib, query_name)
    assert len(matches_name) > 0
    assert matches_name[0].workflow.name == "Study Mode"
    assert matches_name[0].confidence == 1.0
    assert "name" in matches_name[0].matched_fields
    assert matches_name[0].score_breakdown["name_score"] == 0.8


def test_workflow_matcher_partial_overlap_ranking():
    """Checks that overlapping matches are correctly ranked by confidence ratio."""
    lib = WorkflowLibrary()
    matcher = WorkflowMatcher()

    # Query for tags "learn" and "entertainment"
    # "Study Mode" has "learn". "Movie Mode" has "entertainment".
    query_tags = WorkflowMatchQuery(tags=["learn", "entertainment"])
    matches = matcher.match(lib, query_tags)

    assert len(matches) >= 2
    # The confidence should represent the matched tags ratio
    # Study Mode matches 1 out of 2 tags -> score = 0.15, confidence = 0.5
    assert matches[0].confidence == 0.5
    assert "tags" in matches[0].matched_fields


def test_workflow_matcher_input_normalization():
    """Checks that query inputs (ReasoningResult, ObjectiveGraph) normalize successfully."""
    lib = WorkflowLibrary()
    matcher = WorkflowMatcher()

    # Normalize ReasoningResult
    res = ReasoningResult(
        goal_name="STUDY",
        objective=Objective(title="Study Mode", description=""),
        required_capabilities=[],
        constraints=[Constraint(name="Internet", type="internet", description="", satisfied=False)],
        priority=Priority.MEDIUM,
        estimated_complexity="LOW",
    )
    matches_res = matcher.match(lib, res)
    assert len(matches_res) > 0
    assert matches_res[0].workflow.name == "Study Mode"

    # Normalize ObjectiveGraph
    node = ObjectiveNode(
        id="root",
        goal_name="LAUNCH_VSCODE",
        objective=Objective(title="Start Coding", description=""),
    )
    graph = ObjectiveGraph(root_id="root", nodes={"root": node})
    matches_graph = matcher.match(lib, graph)
    assert len(matches_graph) > 0
    assert matches_graph[0].workflow.name == "Start Coding"


def test_task_planner_dependency_injection():
    """Checks that TaskPlanner constructor accepts workflow matching engine injects."""
    lib = WorkflowLibrary()
    matcher = WorkflowMatcher()
    planner = TaskPlanner(workflow_library=lib, workflow_matcher=matcher)

    assert planner._workflow_library is lib
    assert planner._workflow_matcher is matcher
