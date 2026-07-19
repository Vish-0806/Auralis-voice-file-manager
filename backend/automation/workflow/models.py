"""Data models for workflow automation."""

from __future__ import annotations

from typing import Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent


class WorkflowStep(BaseModel):
    """Represents a single atomic operation step in a desktop workflow.

    Attributes:
        intent: The system Intent of the action.
        target: Optional target (like app name or file path).
        parameters: Optional key-value parameters.
    """

    intent: Intent = Field(description="The intent action to execute")
    target: str | None = Field(None, description="Optional target parameter")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Optional execution parameters")


class WorkflowDefinition(BaseModel):
    """Represents the complete definition of a multi-step workflow.

    Attributes:
        name: Name identifier of the workflow.
        description: Description summary of what the workflow does.
        steps: Sequential list of workflow steps to run.
    """

    name: str = Field(description="Name of the workflow")
    description: str = Field(description="Description of the workflow context")
    steps: list[WorkflowStep] = Field(description="Sequential list of actions")
