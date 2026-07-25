"""Objective Graph data models for Auralis Goal Decomposition."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from brain.reasoning.models import Objective


class ObjectiveNode(BaseModel):
    """Represents a single node inside the decomposed objective graph."""

    id: str = Field(description="Unique node identifier, matching the target step ID")
    goal_name: str = Field(description="Target goal or sub-goal name")
    objective: Objective = Field(description="Objective representing the task details")
    dependencies: List[str] = Field(default_factory=list, description="IDs of nodes this node depends on")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")


class ObjectiveGraph(BaseModel):
    """Represents a directed acyclic graph of decomposed objectives."""

    root_id: str = Field(description="ID of the root/final objective node")
    nodes: Dict[str, ObjectiveNode] = Field(default_factory=dict, description="Map of node ID to ObjectiveNode")
