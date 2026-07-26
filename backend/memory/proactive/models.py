"""Pydantic schemas and domain models for Auralis Proactive Recommendations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ProactiveRecommendationDomain(BaseModel):
    """Domain model representing a proactive suggestion recommended to the user."""

    id: Optional[int] = Field(default=None, description="Unique recommendation database key.")
    user_id: int = Field(..., description="Owner user ID.")
    suggestion_text: str = Field(..., description="User-facing recommendation suggestion message.")
    action_type: str = Field(..., description="Execution command action target intent.")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence rank score.")
    scoring_details: Dict[str, Any] = Field(default_factory=dict, description="Metric details breakdown (frequency, recency, etc).")
    status: str = Field(default="pending", description="Lifetime lifecycle status ('pending', 'accepted', 'dismissed', 'ignored').")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PredictionContext(BaseModel):
    """Encapsulates all histories and states passed to the predictor engine."""

    conversations: List[Any] = Field(default_factory=list, description="Recent user-assistant chat exchanges.")
    workflows: List[Any] = Field(default_factory=list, description="Mined workflow definitions/candidates.")
    workspace_info: Dict[str, Any] = Field(default_factory=dict, description="Active directory indicators and profiles.")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Resolved personalization preferences.")
    routines: List[Any] = Field(default_factory=list, description="Registered persistent routine definitions.")
    executions: List[Any] = Field(default_factory=list, description="Historical execution history trace records.")
