"""Unit tests for the Auralis Reasoning Engine subsystem and core Planner integration."""

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
from brain.reasoning.models import Priority, Constraint, Objective, ReasoningResult
from brain.reasoning.objective_builder import ObjectiveBuilder
from brain.reasoning.constraint_analyzer import ConstraintAnalyzer
from brain.reasoning.priority_manager import PriorityManager
from brain.reasoning.reasoning_engine import ReasoningEngine


# --- Models Validation Tests ---

def test_reasoning_models_validation():
    """Validates that Objective, Constraint, and ReasoningResult can be instantiated."""
    obj = Objective(title="Test title", description="Test desc", target="Test target")
    const = Constraint(name="Test constraint", type="test_type", description="Test explanation", satisfied=True)
    res = ReasoningResult(
        goal_name="START_CODING",
        objective=obj,
        required_capabilities=["desktop"],
        constraints=[const],
        priority=Priority.MEDIUM,
        estimated_complexity="MEDIUM"
    )
    assert res.goal_name == "START_CODING"
    assert res.objective.title == "Test title"
    assert len(res.constraints) == 1
    assert res.constraints[0].satisfied is True
    assert res.priority == Priority.MEDIUM
    assert res.estimated_complexity == "MEDIUM"


# --- Objective Builder Tests ---

def test_objective_builder_mapping():
    """Validates mapping of canonical goals to objectives."""
    builder = ObjectiveBuilder()
    
    # Check default goals mapping
    obj_coding = builder.build_objective(Goal(name="START_CODING", category=GoalCategory.DEVELOPMENT, description=""))
    assert "Development" in obj_coding.title or "Workspace" in obj_coding.title
    assert obj_coding.target == "VS Code"

    obj_study = builder.build_objective(Goal(name="STUDY", category=GoalCategory.STUDY, description=""))
    assert obj_study.target == "Study Mode"

    obj_meeting = builder.build_objective(Goal(name="MEETING", category=GoalCategory.PRODUCTIVITY, description=""))
    assert obj_meeting.target == "Meeting Mode"

    obj_downloads = builder.build_objective(Goal(name="ORGANIZE_DOWNLOADS", category=GoalCategory.FILE_MANAGEMENT, description=""))
    assert obj_downloads.target == "Downloads"

    obj_workspace = builder.build_objective(Goal(name="CLEAN_WORKSPACE", category=GoalCategory.PRODUCTIVITY, description=""))
    assert obj_workspace.target == "Workspace"

    obj_app = builder.build_objective(Goal(name="OPEN_APPLICATION", category=GoalCategory.DESKTOP, description="", parameters={"application": "Slack"}))
    assert obj_app.target == "Slack"

    obj_lock = builder.build_objective(Goal(name="LOCK_COMPUTER", category=GoalCategory.SYSTEM_CONTROL, description=""))
    assert obj_lock.target == "PC"

    obj_unknown = builder.build_objective(Goal(name="CUSTOM_GOAL", category=GoalCategory.GENERAL, description="Custom desc"))
    assert obj_unknown.title == "Achieve Objective: Custom_Goal"
    assert obj_unknown.description == "Custom desc"


# --- Constraint Analyzer Tests ---

@patch("brain.reasoning.constraint_analyzer.ConstraintAnalyzer._check_internet_connectivity")
@patch("brain.reasoning.constraint_analyzer.os.path.isdir")
def test_constraint_analyzer(mock_isdir, mock_internet):
    """Validates constraint detection and satisfaction checks."""
    analyzer = ConstraintAnalyzer()
    mock_internet.return_value = True
    mock_isdir.return_value = True

    # 1. Test Internet Dependency (Meeting Goal)
    constraints_meeting = analyzer.analyze_constraints(Goal(name="MEETING", category=GoalCategory.PRODUCTIVITY, description=""))
    assert len(constraints_meeting) == 1
    assert constraints_meeting[0].type == "internet"
    assert constraints_meeting[0].satisfied is True

    # 2. Test File System Check (Organize Downloads Goal)
    constraints_downloads = analyzer.analyze_constraints(Goal(name="ORGANIZE_DOWNLOADS", category=GoalCategory.FILE_MANAGEMENT, description=""))
    assert len(constraints_downloads) == 1
    assert constraints_downloads[0].type == "file_system"
    assert constraints_downloads[0].satisfied is True
    mock_isdir.assert_called_once()

    # 3. Test App Check (Start Coding Goal)
    with patch("brain.reasoning.constraint_analyzer.shutil.which", return_value=True):
        constraints_coding = analyzer.analyze_constraints(Goal(name="START_CODING", category=GoalCategory.DEVELOPMENT, description=""))
        assert len(constraints_coding) == 1
        assert constraints_coding[0].type == "application"
        assert constraints_coding[0].satisfied is True


# --- Priority Manager Tests ---

def test_priority_manager():
    """Validates priority assignment logic."""
    manager = PriorityManager()
    
    assert manager.determine_priority(Goal(name="LOCK_COMPUTER", category=GoalCategory.SYSTEM_CONTROL, description="")) == Priority.CRITICAL
    assert manager.determine_priority(Goal(name="MEETING", category=GoalCategory.PRODUCTIVITY, description="")) == Priority.HIGH
    assert manager.determine_priority(Goal(name="START_CODING", category=GoalCategory.DEVELOPMENT, description="")) == Priority.MEDIUM
    assert manager.determine_priority(Goal(name="ORGANIZE_DOWNLOADS", category=GoalCategory.FILE_MANAGEMENT, description="")) == Priority.LOW
    assert manager.determine_priority(Goal(name="CUSTOM_GOAL", category=GoalCategory.GENERAL, description="")) == Priority.LOW


# --- Reasoning Engine Tests ---

def test_reasoning_engine():
    """Validates core ReasoningEngine orchestrator."""
    engine = ReasoningEngine()
    goal = Goal(name="LOCK_COMPUTER", category=GoalCategory.SYSTEM_CONTROL, description="test lock")
    
    res = engine.reason(goal)
    assert res.goal_name == "LOCK_COMPUTER"
    assert res.priority == Priority.CRITICAL
    assert res.estimated_complexity == "LOW"
    assert "desktop" in res.required_capabilities


# --- Core Planner Integration Tests ---

def test_planner_reasoning_integration():
    """Validates that Planner invokes ReasoningEngine and embeds reasoning metadata in ExecutionPlan parameters."""
    planner = Planner()
    req = AssistantRequest(
        message="start coding",
        source="test",
        timestamp=datetime.now(UTC)
    )
    plan = planner.create_plan(req)
    
    # Verify that plan has reasoning parameters
    assert "reasoning" in plan.parameters
    reasoning_data = plan.parameters["reasoning"]
    assert reasoning_data["objective"]["target"] == "VS Code"
    assert "desktop" in reasoning_data["required_capabilities"]
    assert reasoning_data["priority"] == "MEDIUM"
    assert reasoning_data["estimated_complexity"] == "MEDIUM"
    assert len(reasoning_data["constraints"]) == 1
    assert reasoning_data["constraints"][0]["type"] == "application"


def test_planner_reasoning_defensive_error_handling():
    """Validates that Planner proceeds safely even if the ReasoningEngine throws an exception."""
    mock_reasoning = MagicMock(spec=ReasoningEngine)
    mock_reasoning.reason.side_effect = Exception("Database failure")

    planner = Planner(reasoning_engine=mock_reasoning)
    req = AssistantRequest(
        message="start coding",
        source="test",
        timestamp=datetime.now(UTC)
    )
    plan = planner.create_plan(req)
    
    # Planner should catch the error, write log, and return the ExecutionPlan without reasoning params
    assert plan.intent == Intent.RUN_WORKFLOW
    assert "reasoning" not in plan.parameters
