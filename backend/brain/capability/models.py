"""Data models for Auralis Capability Selection routing.

This module defines models representing selections, routes, requirements,
and routed execution plans compatible with the core ActionDispatcher.
"""

from __future__ import annotations

from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from core.intents import Intent
from core.models import ExecutionPlan as CoreExecutionPlan


class CapabilitySelection(BaseModel):
    """Represents a candidate mapping of an intent/action to a capability.

    Attributes:
        intent: The intent being evaluated.
        capability_name: The name of the resolved capability.
        confidence: Confidence score of the selection.
    """

    intent: Intent = Field(description="The intent action being selected")
    capability_name: str = Field(description="The name of the target capability")
    confidence: float = Field(default=1.0, description="Routing selection confidence")


class CapabilityRoute(BaseModel):
    """Represents a specific route mapping a workflow step to a capability.

    Attributes:
        step_id: Optional step ID identifier within a workflow.
        intent: The step execution action intent.
        capability_name: The name of the routed capability.
    """

    step_id: Optional[str] = Field(None, description="Optional step identifier")
    intent: Intent = Field(description="The execution action intent")
    capability_name: str = Field(description="The target capability name")


class CapabilityRequirement(BaseModel):
    """Represents a structural capability capability requirement dependency.

    Attributes:
        capability_name: The name of the required capability.
        reason: Explanation of why this capability is required.
    """

    capability_name: str = Field(description="The name of the required capability")
    reason: str = Field(description="Explanation of why this capability is required")


class RoutedExecutionPlan(CoreExecutionPlan):
    """Execution plan containing detailed routing metadata for system capabilities.

    Inherits from the core ExecutionPlan model to remain compatible with
    dispatcher verification checks.

    Attributes:
        routes: List of routes mapping steps to capabilities.
        selections: Details of capability selections.
        requirements: Dependencies of capabilities required.
    """

    routes: List[CapabilityRoute] = Field(default_factory=list, description="Capability routes for plan steps")
    selections: List[CapabilitySelection] = Field(default_factory=list, description="Capability selection history")
    requirements: List[CapabilityRequirement] = Field(default_factory=list, description="System capability dependencies")
