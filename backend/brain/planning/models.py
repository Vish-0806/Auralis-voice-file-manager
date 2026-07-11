"""Data models for Auralis Task Planning.

This module defines the models representing execution steps, dependencies,
sequences, and planned execution plans compatible with core execution limits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent


class ExecutionStep(BaseModel):
    """Represents a single step in a task execution sequence.

    Attributes:
        step_id: Unique identifier for this step.
        intent: Core intent of the action.
        target: Optional target argument.
        parameters: Additional parameters for the action.
        can_parallel: Boolean indicating if this step can execute in parallel.
    """

    step_id: str = Field(description="Unique identifier for this step")
    intent: Intent = Field(description="The core Intent representing the action")
    target: Optional[str] = Field(None, description="The target of the action")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    can_parallel: bool = Field(default=False, description="Whether this step can run in parallel with others")


class ExecutionDependency(BaseModel):
    """Represents a dependency relation between steps.

    Attributes:
        step_id: The step that has dependencies.
        depends_on: List of step_ids that this step relies on.
    """

    step_id: str = Field(description="The step that depends on another")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps this step depends on")


class ExecutionSequence(BaseModel):
    """Represents an execution sequence including steps and their dependencies.

    Attributes:
        steps: List of execution steps.
        dependencies: Dependencies governing execution order.
    """

    steps: List[ExecutionStep] = Field(default_factory=list, description="List of execution steps")
    dependencies: List[ExecutionDependency] = Field(default_factory=list, description="List of dependencies")
