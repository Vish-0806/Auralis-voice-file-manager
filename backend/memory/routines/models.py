"""Pydantic schemas and domain models for Auralis Autonomous Routines."""

from datetime import datetime, timezone
from typing import Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class RoutineCandidate(BaseModel):
    """Represents a potential routine identified during pattern analysis."""

    trigger_event: str = Field(..., description="Action trigger name identifying this routine sequence.")
    action_sequence: dict[str, Any] = Field(..., description="Mined steps and configurations parameters.")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Derived accuracy rating.")
    frequency: int = Field(default=0, ge=0, description="Occurrence count of this pattern.")
    avg_interval_seconds: float = Field(default=0.0, ge=0.0, description="Average time difference between triggers.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp.")


class RoutineDefinitionDomain(BaseModel):
    """Domain model representing a persistent, reusable automation routine."""

    id: Optional[int] = Field(default=None, description="Unique routine database key.")
    user_id: int = Field(..., description="Owner user ID.")
    name: str = Field(..., description="User-facing name of the routine.")
    description: Optional[str] = Field(default=None, description="Detailed rationale summary description.")
    steps: list[dict[str, Any]] = Field(default_factory=list, description="Ordered step execution details.")
    trigger_condition: dict[str, Any] = Field(default_factory=dict, description="Criteria parameters mapping triggers.")
    is_active: bool = Field(default=True, description="Active status flag indicator.")
    version: int = Field(default=1, description="Sequential configuration schema version number.")
    metadata_info: dict[str, Any] = Field(default_factory=dict, description="Execution counts, categories, tags, and audit details.")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoutineOptimisationReport(BaseModel):
    """Summary metrics of applied routine step optimization cleanups."""

    original_steps_count: int = Field(..., ge=0, description="Original action steps length.")
    optimised_steps_count: int = Field(..., ge=0, description="Cleaned action steps length.")
    optimisations_applied: list[str] = Field(default_factory=list, description="List of descriptions summarizing fixes.")
    estimated_runtime_reduction_ms: float = Field(default=0.0, description="Estimated saved runtime duration in milliseconds.")


class RoutineRunMetric(BaseModel):
    """Execution performance statistics monitored during runtime."""

    routine_id: int = Field(..., description="Target routine ID.")
    duration_ms: float = Field(..., ge=0.0, description="Run execution duration in milliseconds.")
    success: bool = Field(..., description="Outcome success status indicator.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Observed timestamp.")
