"""Pydantic schemas and orchestration module for Auralis Workflow Recommendations."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkflowRecommendation(BaseModel):
    """Represents a workflow suggestion generated for the user."""

    workflow_id: str = Field(..., description="Deterministic unique identifier for the workflow.")
    workflow_name: str = Field(..., description="Human-readable name of the suggested workflow.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Normalized final recommendation score.")
    recommendation_reason: str = Field(..., description="User-facing rationale explaining why this was suggested.")
    trigger_type: str = Field(..., description="Action trigger type (e.g., adaptive, workspace, preference).")
    suggested_parameters: dict[str, Any] = Field(default_factory=dict, description="Pre-filled context-specific parameters.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Generation timestamp.")


class RecommendationContext(BaseModel):
    """Current user and workspace states used to perform recommendation queries."""

    user_id: int = Field(..., description="Owner user ID.")
    session_id: str = Field(..., description="Active session ID.")
    workspace_analysis: dict[str, Any] = Field(default_factory=dict, description="Active workspace profile analysis stats.")
    resolved_preferences: dict[str, Any] = Field(default_factory=dict, description="Current resolved user preference settings.")
    recent_workflows: list[str] = Field(default_factory=list, description="Chronological history of recently executed workflow names/IDs.")
    current_request: str = Field("", description="Current user text command request query.")
    historical_feedback: dict[str, list[str]] = Field(default_factory=dict, description="Map of workflow_id to list of historical feedback status strings ('accepted', 'rejected', 'ignored').")


class RecommendationScore(BaseModel):
    """Calculated components comprising a workflow recommendation score."""

    frequency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Score based on execution count.")
    recency_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Score based on relative history placement.")
    workspace_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Score based on workspace directory/window matches.")
    preference_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Score based on resolved user preference matches.")
    final_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized weighted sum score.")


class RecommendationConfig(BaseModel):
    """Configuration weights and boundaries for recommendation logic."""

    minimum_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Score threshold filtering.")
    maximum_recommendations: int = Field(default=5, ge=1, description="Upper bounds for recommendation result counts.")
    workspace_weight: float = Field(default=0.3, ge=0.0, description="Weight multiplier for workspace matches.")
    preference_weight: float = Field(default=0.3, ge=0.0, description="Weight multiplier for resolved preferences.")
    frequency_weight: float = Field(default=0.2, ge=0.0, description="Weight multiplier for execution frequency.")
    recency_weight: float = Field(default=0.2, ge=0.0, description="Weight multiplier for relative history recency.")


class RecommendationEngine:
    """Orchestrator for evaluating and recommending workflows using deterministic heuristics."""

    def __init__(self, config: Optional[RecommendationConfig] = None) -> None:
        """Initializes the engine with weight properties."""
        self.config = config or RecommendationConfig()

    def recommend(self, context: RecommendationContext, workflows: list[Any]) -> list[WorkflowRecommendation]:
        """Scores, filters, and ranks workflow recommendations for the context state."""
        if not workflows:
            return []

        scored = self.score_workflows(context, workflows)
        ranked = self.rank(scored)
        filtered = self.filter(ranked)

        recommendations = []
        for wf, score in filtered:
            wf_hash = hashlib.sha256(wf.name.encode("utf-8")).hexdigest()[:12]
            wf_id = f"wf_{wf_hash}"

            reason = "Frequently executed in similar workspace contexts."
            if score.workspace_score > 0.5:
                reason = "Highly aligned with your active workspace activity."
            elif score.preference_score > 0.8:
                reason = "Matches your current environment preferences."

            recommendations.append(
                WorkflowRecommendation(
                    workflow_id=wf_id,
                    workflow_name=wf.name,
                    confidence=score.final_score,
                    recommendation_reason=reason,
                    trigger_type="adaptive",
                    suggested_parameters={},
                    created_at=datetime.now(timezone.utc)
                )
            )
        return recommendations

    def score_workflows(self, context: RecommendationContext, workflows: list[Any]) -> list[Tuple[Any, RecommendationScore]]:
        """Scores each workflow against recent activity, active workspace, and user preferences."""
        scored_list = []

        total_recent = len(context.recent_workflows)
        active_window = context.workspace_analysis.get("active_window", "").lower()
        active_directory = context.workspace_analysis.get("active_directory", "").lower()

        for wf in workflows:
            wf_hash = hashlib.sha256(wf.name.encode("utf-8")).hexdigest()[:12]
            wf_id = f"wf_{wf_hash}"

            # 1. Frequency Score
            if total_recent > 0:
                occurrences = context.recent_workflows.count(wf.name) + context.recent_workflows.count(wf_id)
                frequency_score = min(occurrences / total_recent, 1.0)
            else:
                frequency_score = 0.0

            # 2. Recency Score
            if total_recent > 0:
                idx = -1
                for r_idx, r_wf in enumerate(context.recent_workflows):
                    if r_wf == wf.name or r_wf == wf_id:
                        idx = r_idx
                        break
                if idx != -1:
                    recency_score = (total_recent - idx) / total_recent
                else:
                    recency_score = 0.0
            else:
                recency_score = 0.0

            # 3. Workspace Score
            workspace_matches = 0
            total_comparisons = 0
            for step in getattr(wf, "steps", []):
                target = (getattr(step, "target", None) or "").lower()
                if target:
                    total_comparisons += 1
                    target_words = set(target.split())
                    window_words = set(active_window.split())
                    dir_words = set(active_directory.split())
                    if (target_words & window_words) or (target_words & dir_words) or target in active_window or target in active_directory:
                        workspace_matches += 1
                    else:
                        matched = False
                        for k, v in context.workspace_analysis.items():
                            v_str = str(v).lower()
                            v_words = set(v_str.split())
                            if (target_words & v_words) or target in v_str or v_str in target:
                                matched = True
                                break
                        if matched:
                            workspace_matches += 1
            workspace_score = workspace_matches / total_comparisons if total_comparisons > 0 else 0.0

            # 4. Preference Score
            pref_matches = 0
            pref_checks = 0
            for step in getattr(wf, "steps", []):
                target = (getattr(step, "target", None) or "").lower()
                if target:
                    for category, pref_val in context.resolved_preferences.items():
                        pref_val_str = str(pref_val).lower()
                        if pref_val_str in target or target in pref_val_str:
                            pref_matches += 1
                            pref_checks += 1
                            break
            preference_score = pref_matches / pref_checks if pref_checks > 0 else 1.0

            # 5. Final Normalized Score Calculation
            weight_sum = (
                self.config.frequency_weight +
                self.config.recency_weight +
                self.config.workspace_weight +
                self.config.preference_weight
            )

            if weight_sum > 0:
                final_score = (
                    (frequency_score * self.config.frequency_weight +
                     recency_score * self.config.recency_weight +
                     workspace_score * self.config.workspace_weight +
                     preference_score * self.config.preference_weight) / weight_sum
                )
            else:
                final_score = 0.0

            # Apply historical feedback adjustments to final_score
            feedbacks = context.historical_feedback.get(wf_id, [])
            adjusted_score = final_score
            for fb in feedbacks:
                if fb == "accepted":
                    adjusted_score += 0.1
                elif fb == "rejected":
                    adjusted_score -= 0.2
                elif fb == "ignored":
                    adjusted_score -= 0.05
            
            # Clamp between 0.0 and 1.0
            adjusted_score = max(0.0, min(adjusted_score, 1.0))

            score = RecommendationScore(
                frequency_score=frequency_score,
                recency_score=recency_score,
                workspace_score=workspace_score,
                preference_score=preference_score,
                final_score=adjusted_score
            )
            scored_list.append((wf, score))

        return scored_list

    def rank(self, scored_workflows: list[Tuple[Any, RecommendationScore]]) -> list[Tuple[Any, RecommendationScore]]:
        """Ranks scored workflows descending by final score, using alphabetical workflow ID for tie-breaking."""
        def sorting_key(item: Tuple[Any, RecommendationScore]) -> Tuple[float, str]:
            wf, score = item
            wf_hash = hashlib.sha256(wf.name.encode("utf-8")).hexdigest()[:12]
            wf_id = f"wf_{wf_hash}"
            # Sort final_score descending (using negative value), and ID ascending
            return (-score.final_score, wf_id)

        return sorted(scored_workflows, key=sorting_key)

    def filter(self, ranked_workflows: list[Tuple[Any, RecommendationScore]]) -> list[Tuple[Any, RecommendationScore]]:
        """Filters ranked workflows based on confidence threshold and maximum recommendation count."""
        filtered = [item for item in ranked_workflows if item[1].final_score >= self.config.minimum_confidence]
        return filtered[:self.config.maximum_recommendations]
