"""Data models for Auralis Goal Interpretation.

This module defines the structured models representing high-level user goals,
their categories, and the metadata computed during goal interpretation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class GoalCategory(str, Enum):
    """Categorizes high-level user goals.

    Supported categories group similar goals like development workflows, system controls,
    and file management tasks.
    """

    DEVELOPMENT = "Development"
    PRODUCTIVITY = "Productivity"
    STUDY = "Study"
    ENTERTAINMENT = "Entertainment"
    DESKTOP = "Desktop"
    FILE_MANAGEMENT = "File Management"
    SYSTEM_CONTROL = "System Control"
    GENERAL = "General"


class Goal(BaseModel):
    """Represents a structured user goal.

    Attributes:
        name: The canonical, unique name of the goal (e.g. START_CODING).
        category: The GoalCategory indicating where this goal belongs.
        description: A brief summary explaining the purpose of the goal.
        parameters: Extracted runtime parameters associated with this goal.
    """

    name: str = Field(description="Canonical name of the goal, e.g., START_CODING")
    category: GoalCategory = Field(description="Category of the goal")
    description: str = Field(description="Description of what the goal represents")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted goal parameters")


class GoalConfidence(BaseModel):
    """Represents the confidence of a goal interpretation.

    Attributes:
        score: Floating-point confidence score between 0.0 and 1.0.
        rationale: Explanatory reasoning justifying the computed confidence.
    """

    score: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    rationale: Optional[str] = Field(None, description="Explanation for the computed confidence")


class GoalResult(BaseModel):
    """Represents the output of the goal interpreter.

    Attributes:
        goal: The identified Goal object (or UNKNOWN fallback).
        confidence: Structured confidence score and justification.
        normalized_input: The normalized representation of the interpreted user query.
    """

    goal: Goal = Field(description="The identified Goal object")
    confidence: GoalConfidence = Field(description="Confidence metrics for the identified goal")
    normalized_input: str = Field(description="The normalized text input that was interpreted")
