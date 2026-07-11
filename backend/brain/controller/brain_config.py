"""Centralized configuration for the Auralis AI Brain Controller."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class BrainConfig(BaseModel):
    """Centralized configuration values for Auralis AI Brain pipelines.

    Attributes:
        confidence_threshold: Goal interpreter confidence threshold.
        recovery_enabled: Whether to auto-apply recovery fallbacks.
        recovery_policy: Mapping or name of active recovery policy.
        monitoring_enabled: Enable progress tracking metrics events.
        stalled_threshold_seconds: Step timeout threshold signaling stall warnings.
        planning_strategy: Active planning algorithm.
        execution_strategy: Active scheduling algorithm.
    """

    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for interpreted goals")
    recovery_enabled: bool = Field(default=True, description="Enable automatic self-correction recovery")
    recovery_policy: str = Field(default="DEFAULT", description="Name of recovery policy")
    monitoring_enabled: bool = Field(default=True, description="Enable observational progress monitoring")
    stalled_threshold_seconds: float = Field(default=5.0, description="Step duration stall warning threshold")
    planning_strategy: str = Field(default="TOPOLOGICAL", description="Dynamic task planner logic")
    execution_strategy: str = Field(default="SEQUENTIAL", description="Execution scheduling strategy")
