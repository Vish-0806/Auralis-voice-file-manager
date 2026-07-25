"""Unit tests for the Goal Decomposition subsystem in Auralis."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
import pytest
from brain.reasoning.models import Objective, Constraint, Priority, ReasoningResult
from brain.planning.objective_graph import ObjectiveNode, ObjectiveGraph
from brain.planning.decomposition_validator import DecompositionValidator
from brain.planning.decomposition_rules import DecompositionRules
from brain.planning.goal_decomposer import GoalDecomposer


def test_objective_graph_schema_validation():
    """Validates that ObjectiveNode and ObjectiveGraph schemas instantiate properly."""
    node = ObjectiveNode(
        id="test_node",
        goal_name="TEST_GOAL",
        objective=Objective(title="Test Node", description="Test description"),
        dependencies=["parent_node"],
    )
    graph = ObjectiveGraph(root_id="test_node", nodes={"test_node": node})

    assert graph.root_id == "test_node"
    assert "test_node" in graph.nodes
    assert graph.nodes["test_node"].goal_name == "TEST_GOAL"
    assert "parent_node" in graph.nodes["test_node"].dependencies


def test_decomposition_rules_standard_goals():
    """Validates that DecompositionRules maps goals into expected sub-objectives."""
    rules = DecompositionRules()

    # Test LOCK_COMPUTER
    res_lock = ReasoningResult(
        goal_name="LOCK_COMPUTER",
        objective=Objective(title="Secure Computer", description="Lock session"),
        required_capabilities=["desktop"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW",
    )
    graph_lock = rules.decompose(res_lock)
    assert graph_lock.root_id == "step_lock_pc"
    assert len(graph_lock.nodes) == 1
    assert graph_lock.nodes["step_lock_pc"].goal_name == "LOCK_COMPUTER"

    # Test START_CODING
    res_code = ReasoningResult(
        goal_name="START_CODING",
        objective=Objective(title="Code Session", description="Coding Mode"),
        required_capabilities=["desktop", "workflow"],
        constraints=[],
        priority=Priority.MEDIUM,
        estimated_complexity="MEDIUM",
    )
    graph_code = rules.decompose(res_code)
    assert graph_code.root_id == "step_set_volume"
    assert len(graph_code.nodes) == 3
    assert "step_launch_vscode" in graph_code.nodes
    assert "step_launch_terminal" in graph_code.nodes
    assert "step_set_volume" in graph_code.nodes
    assert "step_launch_vscode" in graph_code.nodes["step_launch_terminal"].dependencies
    assert "step_launch_terminal" in graph_code.nodes["step_set_volume"].dependencies


def test_decomposition_rules_constraints_injection():
    """Validates that unsatisfied constraints inject appropriate prep nodes."""
    rules = DecompositionRules()
    
    # Unsatisfied internet constraint in MEETING mode
    c_internet = Constraint(name="Internet", type="internet", description="", satisfied=False)
    res_meeting = ReasoningResult(
        goal_name="MEETING",
        objective=Objective(title="Join Meeting", description="Meeting Mode"),
        required_capabilities=["desktop", "workflow"],
        constraints=[c_internet],
        priority=Priority.HIGH,
        estimated_complexity="MEDIUM",
    )
    graph_meeting = rules.decompose(res_meeting)
    
    # Checks that prep_enable_wifi is injected
    assert "prep_enable_wifi" in graph_meeting.nodes
    assert graph_meeting.nodes["prep_enable_wifi"].goal_name == "PREP_WIFI"
    
    # Action nodes must list prep_enable_wifi in their dependencies
    assert "prep_enable_wifi" in graph_meeting.nodes["step_show_desktop"].dependencies
    assert "prep_enable_wifi" in graph_meeting.nodes["step_launch_notepad"].dependencies


def test_decomposition_validator_cycle_detection():
    """Validates that DecompositionValidator correctly raises ValueError when cycles are present."""
    validator = DecompositionValidator()

    # Valid graph (A depends on B)
    node_a = ObjectiveNode(
        id="A",
        goal_name="A_GOAL",
        objective=Objective(title="A", description=""),
        dependencies=["B"],
    )
    node_b = ObjectiveNode(
        id="B",
        goal_name="B_GOAL",
        objective=Objective(title="B", description=""),
        dependencies=[],
    )
    graph_valid = ObjectiveGraph(root_id="A", nodes={"A": node_a, "B": node_b})
    validator.validate(graph_valid)  # Should pass without error

    # Cyclic graph (A depends on B, B depends on A)
    node_a_cyclic = ObjectiveNode(
        id="A",
        goal_name="A_GOAL",
        objective=Objective(title="A", description=""),
        dependencies=["B"],
    )
    node_b_cyclic = ObjectiveNode(
        id="B",
        goal_name="B_GOAL",
        objective=Objective(title="B", description=""),
        dependencies=["A"],
    )
    graph_cyclic = ObjectiveGraph(root_id="A", nodes={"A": node_a_cyclic, "B": node_b_cyclic})
    with pytest.raises(ValueError) as excinfo:
        validator.validate(graph_cyclic)
    assert "Circular dependency detected" in str(excinfo.value)

    # Missing node dependency reference
    node_missing_dep = ObjectiveNode(
        id="A",
        goal_name="A_GOAL",
        objective=Objective(title="A", description=""),
        dependencies=["NON_EXISTENT"],
    )
    graph_missing = ObjectiveGraph(root_id="A", nodes={"A": node_missing_dep})
    with pytest.raises(ValueError) as excinfo:
        validator.validate(graph_missing)
    assert "not found in graph" in str(excinfo.value)


def test_goal_decomposer_integration():
    """Validates that GoalDecomposer successfully orchestrates decomposition and validation."""
    decomposer = GoalDecomposer()

    res = ReasoningResult(
        goal_name="LOCK_COMPUTER",
        objective=Objective(title="Lock computer", description=""),
        required_capabilities=["desktop"],
        constraints=[],
        priority=Priority.CRITICAL,
        estimated_complexity="LOW",
    )
    graph = decomposer.decompose(res)
    assert isinstance(graph, ObjectiveGraph)
    assert graph.root_id == "step_lock_pc"
