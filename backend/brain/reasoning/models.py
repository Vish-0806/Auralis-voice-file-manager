"""Data models for Auralis Goal Reasoning.

This module defines the structured models representing high-level user objectives,
priority levels, system constraints, and reasoning results.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    """Supported priority levels for execution scheduling."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Constraint(BaseModel):
    """Immutable model representing a system or capability dependency/constraint."""

    model_config = ConfigDict(frozen=True)

    constraint_type: str = "UNKNOWN"
    value: str = ""
    severity: str = "NORMAL"
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Legacy attributes for backward compatibility
    name: str = Field(default="", description="Name or identifier of the constraint")
    type: str = Field(default="", description="Type of constraint (e.g., internet, application, permission, file_system)")
    description: str = Field(default="", description="Explanation of the constraint")
    satisfied: bool = Field(default=True, description="Whether the constraint is currently met")


class Objective(BaseModel):
    """Represents a high-level translated user objective."""

    title: str = Field(description="Summary title of the objective")
    description: str = Field(description="Detailed explanation of the objective")
    target: Optional[str] = Field(None, description="The primary target resource, file, or application")


class ReasoningResult(BaseModel):
    """Represents the output of the reasoning engine analysis."""

    goal_name: str = Field(description="Name of the source goal")
    objective: Objective = Field(description="Structured high-level objective details")
    required_capabilities: List[str] = Field(default_factory=list, description="Capabilities required for execution")
    constraints: List[Constraint] = Field(default_factory=list, description="Analyzed dependencies/constraints")
    priority: Priority = Field(description="Assigned priority for this goal")
    estimated_complexity: str = Field(description="Estimated complexity rating (e.g., LOW, MEDIUM, HIGH)")
