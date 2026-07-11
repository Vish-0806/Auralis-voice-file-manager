"""Data models for Auralis Goal Reasoning.

This module defines the structured models representing high-level user objectives,
priority levels, system constraints, and reasoning results.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Supported priority levels for execution scheduling."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Constraint(BaseModel):
    """Represents a system or capability dependency/constraint.

    Attributes:
        name: Name of the constraint.
        type: Type of constraint (e.g. internet, application, permission, file_system).
        description: Description of the constraint and its purpose.
        satisfied: Boolean indicating whether the dependency is met.
    """

    name: str = Field(description="Name or identifier of the constraint")
    type: str = Field(description="Type of constraint (e.g., internet, application, permission, file_system)")
    description: str = Field(description="Explanation of the constraint")
    satisfied: bool = Field(default=True, description="Whether the constraint is currently met")


class Objective(BaseModel):
    """Represents a high-level translated user objective.

    Attributes:
        title: Short title of the objective.
        description: Informative description of the objective goals.
        target: Optional target component, directory, or app.
    """

    title: str = Field(description="Summary title of the objective")
    description: str = Field(description="Detailed explanation of the objective")
    target: Optional[str] = Field(None, description="The primary target resource, file, or application")


class ReasoningResult(BaseModel):
    """Represents the output of the reasoning engine analysis.

    Attributes:
        goal_name: The name of the Goal that was analyzed.
        objective: The mapped high-level Objective.
        required_capabilities: Capabilities required to achieve this goal.
        constraints: Detected system constraints/dependencies.
        priority: The assigned priority.
        estimated_complexity: Complexity estimation (e.g. LOW, MEDIUM, HIGH).
    """

    goal_name: str = Field(description="Name of the source goal")
    objective: Objective = Field(description="Structured high-level objective details")
    required_capabilities: List[str] = Field(default_factory=list, description="Capabilities required for execution")
    constraints: List[Constraint] = Field(default_factory=list, description="Analyzed dependencies/constraints")
    priority: Priority = Field(description="Assigned priority for this goal")
    estimated_complexity: str = Field(description="Estimated complexity rating (e.g., LOW, MEDIUM, HIGH)")
