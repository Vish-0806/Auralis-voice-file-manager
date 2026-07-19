"""Unit tests for Auralis Goal Interpretation subsystem and Planner integration.

This module validates that Goal Models, Classifier, Registry, Interpreter,
and Planner integration behave correctly under various conditions.
"""

from __future__ import annotations

import os
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock
# pyrefly: ignore [missing-import]
import pytest

from core.models import AssistantRequest, SessionContext
from core.intents import Intent
from core.planner import Planner
from brain.goal.models import Goal, GoalCategory, GoalConfidence, GoalResult
from brain.goal.goal_classifier import GoalClassifier
from brain.goal.goal_registry import GoalRegistry
from brain.goal.goal_interpreter import GoalInterpreter


# --- Goal Models & Category Tests ---

def test_goal_models_validation():
    """Validates that Goal and GoalResult models can be instantiated and validated."""
    goal = Goal(
        name="CUSTOM_GOAL",
        category=GoalCategory.DEVELOPMENT,
        description="A test custom goal",
        parameters={"param1": "value1"}
    )
    assert goal.name == "CUSTOM_GOAL"
    assert goal.category == GoalCategory.DEVELOPMENT
    assert goal.parameters == {"param1": "value1"}

    confidence = GoalConfidence(score=0.85, rationale="Matched keyword custom")
    result = GoalResult(
        goal=goal,
        confidence=confidence,
        normalized_input="run custom workflow"
    )
    assert result.goal == goal
    assert result.confidence.score == 0.85
    assert result.normalized_input == "run custom workflow"


# --- Goal Classifier Tests ---

def test_goal_classifier_classify_goal():
    """Validates classification of canonical goal names."""
    classifier = GoalClassifier()
    assert classifier.classify_goal("START_CODING") == GoalCategory.DEVELOPMENT
    assert classifier.classify_goal("STUDY") == GoalCategory.STUDY
    assert classifier.classify_goal("MEETING") == GoalCategory.PRODUCTIVITY
    assert classifier.classify_goal("ORGANIZE_DOWNLOADS") == GoalCategory.FILE_MANAGEMENT
    assert classifier.classify_goal("CLEAN_WORKSPACE") == GoalCategory.PRODUCTIVITY
    assert classifier.classify_goal("OPEN_APPLICATION") == GoalCategory.DESKTOP
    assert classifier.classify_goal("LOCK_COMPUTER") == GoalCategory.SYSTEM_CONTROL
    assert classifier.classify_goal("UNKNOWN_GOAL") == GoalCategory.GENERAL


def test_goal_classifier_classify_text():
    """Validates heuristic text-based category classification."""
    classifier = GoalClassifier()
    assert classifier.classify_text("i want to write some python code") == GoalCategory.DEVELOPMENT
    assert classifier.classify_text("prepare for learning new math") == GoalCategory.STUDY
    assert classifier.classify_text("start the zoom call") == GoalCategory.PRODUCTIVITY
    assert classifier.classify_text("sort my files inside downloads folder") == GoalCategory.FILE_MANAGEMENT
    assert classifier.classify_text("open application calculator") == GoalCategory.DESKTOP
    assert classifier.classify_text("lock my computer session") == GoalCategory.SYSTEM_CONTROL
    assert classifier.classify_text("what is the weather today") == GoalCategory.GENERAL


# --- Goal Registry Tests ---

def test_goal_registry_default_goals():
    """Validates that default goals are initialized inside the registry."""
    registry = GoalRegistry()
    assert registry.get_goal("START_CODING") is not None
    assert registry.get_goal("STUDY") is not None
    assert registry.get_goal("MEETING") is not None
    assert registry.get_goal("ORGANIZE_DOWNLOADS") is not None
    assert registry.get_goal("CLEAN_WORKSPACE") is not None
    assert registry.get_goal("OPEN_APPLICATION") is not None
    assert registry.get_goal("LOCK_COMPUTER") is not None
    assert registry.get_goal("UNKNOWN") is not None

    goals = registry.list_goals()
    assert len(goals) >= 8


def test_goal_registry_custom_registration():
    """Validates registration of custom goals."""
    registry = GoalRegistry()
    custom_goal = Goal(
        name="RUN_BACKUP",
        category=GoalCategory.SYSTEM_CONTROL,
        description="Backup all local workspaces"
    )
    registry.register_goal(custom_goal)
    assert registry.get_goal("RUN_BACKUP") == custom_goal


# --- Goal Interpreter Tests ---

def test_goal_interpreter_normalization():
    """Validates that the input normalization removes extra whitespace and is case-insensitive."""
    interpreter = GoalInterpreter()
    assert interpreter.normalize_input("  Start   Coding  ") == "start coding"
    assert interpreter.normalize_input("\tStudy\nMode  ") == "study mode"
    assert interpreter.normalize_input("") == ""


def test_goal_interpreter_exact_matches():
    """Validates that exact patterns match with 1.0 confidence score."""
    interpreter = GoalInterpreter()
    
    # START_CODING
    res1 = interpreter.interpret("Start coding now")
    assert res1.goal.name == "START_CODING"
    assert res1.confidence.score == 1.0

    # STUDY
    res2 = interpreter.interpret("Time to study")
    assert res2.goal.name == "STUDY"
    assert res2.confidence.score == 1.0

    # MEETING
    res3 = interpreter.interpret("Start meeting mode")
    assert res3.goal.name == "MEETING"
    assert res3.confidence.score == 1.0

    # ORGANIZE_DOWNLOADS
    res4 = interpreter.interpret("organize downloads")
    assert res4.goal.name == "ORGANIZE_DOWNLOADS"
    assert res4.confidence.score == 1.0

    # CLEAN_WORKSPACE
    res5 = interpreter.interpret("clean workspace")
    assert res5.goal.name == "CLEAN_WORKSPACE"
    assert res5.confidence.score == 1.0

    # LOCK_COMPUTER
    res6 = interpreter.interpret("lock pc")
    assert res6.goal.name == "LOCK_COMPUTER"
    assert res6.confidence.score == 1.0


def test_goal_interpreter_keyword_matches():
    """Validates keyword matching proximity and scoring logic."""
    interpreter = GoalInterpreter()
    res = interpreter.interpret("I want to do some programming and open my IDE")
    assert res.goal.name == "START_CODING"
    assert 0.5 <= res.confidence.score <= 0.8


def test_goal_interpreter_parameter_extraction():
    """Validates application name extraction for OPEN_APPLICATION goal."""
    interpreter = GoalInterpreter()
    res1 = interpreter.interpret("open app vs code")
    assert res1.goal.name == "OPEN_APPLICATION"
    assert res1.goal.parameters == {"application": "vs code"}

    res2 = interpreter.interpret("launch application slack")
    assert res2.goal.name == "OPEN_APPLICATION"
    assert res2.goal.parameters == {"application": "slack"}

    # Edge cases
    res3 = interpreter.interpret("open folder documents")
    # Should fall back to unknown/other since folder documents is blacklisted for application name
    assert res3.goal.name != "OPEN_APPLICATION"


def test_goal_interpreter_unknown_fallback():
    """Validates fallback to UNKNOWN and general category prediction."""
    interpreter = GoalInterpreter()
    res1 = interpreter.interpret("what is 2 + 2")
    assert res1.goal.name == "UNKNOWN"
    assert res1.goal.category == GoalCategory.GENERAL
    assert res1.confidence.score == 0.0

    res2 = interpreter.interpret("i want to check my homework assignments")
    assert res2.goal.name == "UNKNOWN"
    # Classified category should heuristically be predicted as STUDY
    assert res2.goal.category == GoalCategory.STUDY
    assert res2.confidence.score == 0.3


# --- Core Planner Integration Tests ---

def test_planner_goal_interpreter_bypass():
    """Validates that Planner uses GoalInterpreter and bypasses rule parsing when confidence >= threshold."""
    # Mock interpreter returning high-confidence MATCH
    mock_goal = Goal(
        name="START_CODING",
        category=GoalCategory.DEVELOPMENT,
        description="test",
        parameters={}
    )
    mock_result = GoalResult(
        goal=mock_goal,
        confidence=GoalConfidence(score=0.9, rationale="test"),
        normalized_input="start coding"
    )
    mock_interpreter = MagicMock(spec=GoalInterpreter)
    mock_interpreter.interpret.return_value = mock_result

    planner = Planner(goal_interpreter=mock_interpreter, goal_threshold=0.8)
    req = AssistantRequest(message="start coding", source="test", timestamp=datetime.now(UTC))
    
    plan = planner.create_plan(req)
    assert plan.intent == Intent.RUN_WORKFLOW
    assert plan.target == "Start Coding"
    assert plan.confidence == 0.9
    mock_interpreter.interpret.assert_called_once_with("start coding")


def test_planner_goal_interpreter_fallback_below_threshold():
    """Validates that Planner falls back to standard regex rules if goal interpreter confidence < threshold."""
    mock_goal = Goal(
        name="START_CODING",
        category=GoalCategory.DEVELOPMENT,
        description="test",
        parameters={}
    )
    # Confidence is 0.6, threshold is 0.8
    mock_result = GoalResult(
        goal=mock_goal,
        confidence=GoalConfidence(score=0.6, rationale="test"),
        normalized_input="start coding"
    )
    mock_interpreter = MagicMock(spec=GoalInterpreter)
    mock_interpreter.interpret.return_value = mock_result

    planner = Planner(goal_interpreter=mock_interpreter, goal_threshold=0.8)
    # The request "lock pc" should fall back to existing planner rules and be identified as LOCK_PC
    req = AssistantRequest(message="lock pc", source="test", timestamp=datetime.now(UTC))
    
    plan = planner.create_plan(req)
    assert plan.intent == Intent.LOCK_PC
    assert plan.confidence == 0.75
    mock_interpreter.interpret.assert_called_once_with("lock pc")


def test_planner_goal_interpreter_fallback_unknown_goal():
    """Validates that Planner falls back to standard regex rules if goal is interpreted as UNKNOWN."""
    mock_goal = Goal(
        name="UNKNOWN",
        category=GoalCategory.GENERAL,
        description="test",
        parameters={}
    )
    # Confidence score is 0.9 (above threshold) but goal name is UNKNOWN
    mock_result = GoalResult(
        goal=mock_goal,
        confidence=GoalConfidence(score=0.9, rationale="test"),
        normalized_input="lock pc"
    )
    mock_interpreter = MagicMock(spec=GoalInterpreter)
    mock_interpreter.interpret.return_value = mock_result

    planner = Planner(goal_interpreter=mock_interpreter, goal_threshold=0.8)
    req = AssistantRequest(message="lock pc", source="test", timestamp=datetime.now(UTC))
    
    plan = planner.create_plan(req)
    assert plan.intent == Intent.LOCK_PC
    assert plan.confidence == 0.75
    mock_interpreter.interpret.assert_called_once_with("lock pc")


def test_planner_goal_interpreter_defensive_error_handling():
    """Validates that Planner falls back safely if GoalInterpreter throws an exception."""
    mock_interpreter = MagicMock(spec=GoalInterpreter)
    mock_interpreter.interpret.side_effect = Exception("Mocked database error")

    planner = Planner(goal_interpreter=mock_interpreter, goal_threshold=0.7)
    req = AssistantRequest(message="lock pc", source="test", timestamp=datetime.now(UTC))
    
    # Planner should swallow the exception and run normal rules
    plan = planner.create_plan(req)
    assert plan.intent == Intent.LOCK_PC
    assert plan.confidence == 0.75


@patch.dict(os.environ, {"AURALIS_GOAL_THRESHOLD": "0.5"})
def test_planner_goal_threshold_env_configuration():
    """Validates that threshold is configured via AURALIS_GOAL_THRESHOLD environment variable."""
    # When threshold env variable is set to 0.5, a confidence of 0.6 is accepted
    mock_goal = Goal(
        name="START_CODING",
        category=GoalCategory.DEVELOPMENT,
        description="test",
        parameters={}
    )
    mock_result = GoalResult(
        goal=mock_goal,
        confidence=GoalConfidence(score=0.6, rationale="test"),
        normalized_input="start coding"
    )
    mock_interpreter = MagicMock(spec=GoalInterpreter)
    mock_interpreter.interpret.return_value = mock_result

    # Let the constructor check env
    planner = Planner(goal_interpreter=mock_interpreter)
    assert planner._goal_threshold == 0.5

    req = AssistantRequest(message="start coding", source="test", timestamp=datetime.now(UTC))
    plan = planner.create_plan(req)
    assert plan.intent == Intent.RUN_WORKFLOW
    assert plan.target == "Start Coding"
    assert plan.confidence == 0.6
