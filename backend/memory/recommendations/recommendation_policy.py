"""Recommendation policy engine module to filter suggestion displays."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RecommendationCooldown(BaseModel):
    """Represents an active cooldown window for a specific workflow suggestion."""

    workflow_id: str = Field(..., description="Target workflow ID.")
    cooldown_until: datetime = Field(..., description="Timestamp when the cooldown ends.")


class RecommendationPolicy(BaseModel):
    """Defines presentation control limits for suggested workflows."""

    minimum_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold.")
    cooldown_duration_seconds: int = Field(default=300, ge=0, description="Default duration in seconds for rejection/shown cooldowns.")
    suppress_duplicates: bool = Field(default=True, description="True to suppress recently shown recommendations.")
    maximum_recommendations: int = Field(default=5, ge=1, description="Upper bound count for suggestions list.")


class RecommendationDecision(BaseModel):
    """Result decision detailing whether a recommendation should be shown."""

    should_show: bool = Field(..., description="True if the recommendation should be shown.")
    reason: str = Field(..., description="Rationale explaining the policy decision.")
    decision_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the decision.")


class RecommendationPolicyEngine:
    """Policy engine enforcing confidence, cooldown, duplicate suppression, and limits."""

    def __init__(self, policy: Optional[RecommendationPolicy] = None) -> None:
        """Initializes the policy engine with rejection, shown, and active cooldown trackers."""
        self.policy = policy or RecommendationPolicy()
        self.rejection_history: dict[str, datetime] = {}
        self.shown_history: dict[str, datetime] = {}
        self.active_cooldowns: dict[str, datetime] = {}

    def evaluate_policy(self, recommendation: Any, current_time: Optional[datetime] = None) -> RecommendationDecision:
        """Evaluates whether a single workflow recommendation satisfies the policy rules."""
        now = current_time or datetime.now(timezone.utc)

        # 1. Enforce Confidence Threshold Check
        if recommendation.confidence < self.policy.minimum_confidence:
            return RecommendationDecision(
                should_show=False,
                reason="Below minimum confidence threshold.",
                decision_at=now
            )

        # 2. Enforce Active Cooldown Check
        cooldown_until = self.active_cooldowns.get(recommendation.workflow_id)
        if cooldown_until and now < cooldown_until:
            return RecommendationDecision(
                should_show=False,
                reason="Workflow is in active cooldown period.",
                decision_at=now
            )

        # 3. Enforce Rejection History Check
        last_rejected = self.rejection_history.get(recommendation.workflow_id)
        if last_rejected:
            elapsed = (now - last_rejected).total_seconds()
            if elapsed < self.policy.cooldown_duration_seconds:
                return RecommendationDecision(
                    should_show=False,
                    reason="Workflow recently rejected by user.",
                    decision_at=now
                )

        # 4. Enforce Shown / Duplicate Suppression Check
        if self.policy.suppress_duplicates:
            last_shown = self.shown_history.get(recommendation.workflow_id)
            if last_shown:
                elapsed = (now - last_shown).total_seconds()
                if elapsed < self.policy.cooldown_duration_seconds:
                    return RecommendationDecision(
                        should_show=False,
                        reason="Workflow recently shown (duplicate suppression).",
                        decision_at=now
                    )

        # 5. Otherwise, Show Recommendation
        return RecommendationDecision(
            should_show=True,
            reason="Passes all policy guidelines.",
            decision_at=now
        )

    def record_rejection(self, workflow_id: str, timestamp: Optional[datetime] = None) -> None:
        """Records a user rejection event for a workflow ID."""
        t = timestamp or datetime.now(timezone.utc)
        self.rejection_history[workflow_id] = t

    def record_shown(self, workflow_id: str, timestamp: Optional[datetime] = None) -> None:
        """Records a workflow recommendation presentation event."""
        t = timestamp or datetime.now(timezone.utc)
        self.shown_history[workflow_id] = t

    def add_cooldown(self, workflow_id: str, duration_seconds: int, current_time: Optional[datetime] = None) -> None:
        """Places a workflow ID into an active cooldown window."""
        now = current_time or datetime.now(timezone.utc)
        self.active_cooldowns[workflow_id] = now + timedelta(seconds=duration_seconds)
