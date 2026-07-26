"""User Preference Learning subsystem for Auralis memory."""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator

from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryType, AssistantContext

logger = logging.getLogger(__name__)


def ensure_utc(v: Optional[datetime]) -> Optional[datetime]:
    """Helper to ensure datetime objects are timezone-aware and set to UTC."""
    if v is None:
        return None
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v.astimezone(timezone.utc)


class PreferenceObservation(BaseModel):
    """Represents a single captured user choice, execution instance, or explicit override."""

    user_id: int = Field(..., description="ID of the associated user")
    category: str = Field(..., description="Preference category (e.g., 'Browser', 'IDE', 'Shell')")
    value: Any = Field(..., description="The chosen option or parameter value (e.g., 'Chrome', 'VS Code')")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the action occurred"
    )
    is_override: bool = Field(
        default=False,
        description="True if the user explicitly overrode a predicted preference"
    )
    execution_id: Optional[str] = Field(
        default=None, 
        description="Reference to the ExecutionHistory ID if triggered by an automated plan execution"
    )
    execution_status: str = Field(
        default="SUCCESS",
        description="The outcome status of the execution (e.g., 'SUCCESS', 'COMPLETED', 'FAILED')"
    )
    context_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional context at the time of execution (e.g., OS environment, active window)"
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v


class PreferenceCandidate(BaseModel):
    """Represents a value under evaluation for promotion to a stable user preference."""

    user_id: int = Field(..., description="ID of the user")
    category: str = Field(..., description="Category of preference")
    value: Any = Field(..., description="Candidate preference value")
    observation_count: int = Field(default=1, description="Total observations of this value")
    success_count: int = Field(default=0, description="Total successful executions containing this value")
    first_observed: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="First timestamp this candidate was seen"
    )
    last_observed: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Most recent timestamp this candidate was seen"
    )
    is_explicit: bool = Field(default=False, description="True if forced by explicit user override action")

    @field_validator("first_observed", "last_observed", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v


class ResolvedPreference(BaseModel):
    """Represents the active, resolved preference for a category to be applied during planning."""

    user_id: int = Field(..., description="ID of the user")
    category: str = Field(..., description="Preference category")
    value: Any = Field(..., description="Resolved option value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Resolved confidence score")
    resolved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when preference was resolved"
    )
    source: str = Field(
        ..., 
        description="Origin of preference: 'explicit_override', 'learned_stable', 'default_fallback'"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trace info (e.g., observation count, conflict resolution parameters)"
    )

    @field_validator("resolved_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Any:
        if isinstance(v, datetime):
            return ensure_utc(v)
        return v


class PreferenceStatistics(BaseModel):
    """Analytical rollup details for monitoring learning rates and pattern health."""

    user_id: int = Field(..., description="ID of the user")
    category: str = Field(..., description="Preference category")
    total_observations: int = Field(..., description="Cumulative observation data points")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of successful runs")
    override_rate: float = Field(..., ge=0.0, le=1.0, description="Frequency of explicit corrections")
    decayed_recency_score: float = Field(..., ge=0.0, le=1.0, description="Time-decayed score of interactions")
    frequency_score: float = Field(..., ge=0.0, le=1.0, description="Normalized occurrence volume")


class PreferenceScorer:
    """Calculates numerical confidence for candidate preference options."""

    def __init__(
        self, 
        w_frequency: float = 0.3,
        w_recency: float = 0.3,
        w_success: float = 0.2,
        w_override: float = 0.2,
        half_life_seconds: float = 86400.0,
        saturation_count: int = 5
    ) -> None:
        self.w_frequency = w_frequency
        self.w_recency = w_recency
        self.w_success = w_success
        self.w_override = w_override
        self.half_life_seconds = half_life_seconds
        self.saturation_count = saturation_count

    def compute_score(
        self, 
        candidate: PreferenceCandidate, 
        recent_observations: List[PreferenceObservation],
        current_time: Optional[datetime] = None
    ) -> float:
        """Calculates confidence score based on frequency, recency, success, and overrides.
        
        Score is in the range 0.0 -> 1.0.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        current_time = ensure_utc(current_time)

        # Filter observations for this specific candidate's value
        obs_list = [
            o for o in recent_observations
            if o.category.strip().lower() == candidate.category.strip().lower()
            and str(o.value).strip().lower() == str(candidate.value).strip().lower()
        ]

        if not obs_list:
            return 0.0

        # 1. Frequency Score (S_freq)
        obs_count = len(obs_list)
        s_freq = min(1.0, obs_count / max(1, self.saturation_count))

        # 2. Recency Score (S_rec)
        last_obs_time = max(ensure_utc(o.timestamp) for o in obs_list)
        delta_t = (current_time - last_obs_time).total_seconds()
        delta_t = max(0.0, delta_t)
        
        decay_rate = math.log(2.0) / max(1.0, self.half_life_seconds)
        s_rec = math.exp(-decay_rate * delta_t)

        # 3. Success Rate (S_succ)
        successes = sum(
            1 for o in obs_list 
            if o.is_override or o.execution_status.upper() in ["SUCCESS", "COMPLETED"]
        )
        s_succ = successes / obs_count if obs_count > 0 else 0.0

        # 4. Explicit Override (S_over)
        s_over = 1.0 if any(o.is_override for o in obs_list) else 0.0

        # Compute weighted sum
        total_weight = self.w_frequency + self.w_recency + self.w_success + self.w_override
        if total_weight <= 0.0:
            return 0.0

        raw_score = (
            self.w_frequency * s_freq
            + self.w_recency * s_rec
            + self.w_success * s_succ
            + self.w_override * s_over
        )
        
        score = raw_score / total_weight
        return max(0.0, min(1.0, score))


class PreferenceLearner:
    """Evaluates observation history streams to identify stable user preferences."""

    def __init__(self, stabilization_threshold: float = 0.7) -> None:
        self.stabilization_threshold = stabilization_threshold

    def extract_candidates(
        self, 
        observations: List[PreferenceObservation]
    ) -> List[PreferenceCandidate]:
        """Groups historical observations into candidates with frequency/success metrics."""
        if not observations:
            return []

        groups: Dict[tuple, Dict[str, Any]] = {}
        for obs in observations:
            user_id = obs.user_id
            cat = obs.category.strip()
            val_str = str(obs.value).strip().lower()
            key = (user_id, cat, val_str)

            if key not in groups:
                groups[key] = {
                    "user_id": user_id,
                    "category": cat,
                    "value": obs.value,
                    "observations": [],
                }
            groups[key]["observations"].append(obs)

        candidates = []
        for key, info in groups.items():
            obs_list = info["observations"]
            obs_count = len(obs_list)
            success_count = sum(
                1 for o in obs_list 
                if o.is_override or o.execution_status.upper() in ["SUCCESS", "COMPLETED"]
            )
            timestamps = [ensure_utc(o.timestamp) for o in obs_list]
            first_observed = min(timestamps)
            last_observed = max(timestamps)
            is_explicit = any(o.is_override for o in obs_list)

            candidate = PreferenceCandidate(
                user_id=info["user_id"],
                category=info["category"],
                value=info["value"],
                observation_count=obs_count,
                success_count=success_count,
                first_observed=first_observed,
                last_observed=last_observed,
                is_explicit=is_explicit,
            )
            candidates.append(candidate)

        return candidates

    def evaluate_stability(
        self, 
        candidate: PreferenceCandidate, 
        scorer: PreferenceScorer,
        observations: List[PreferenceObservation],
        current_time: Optional[datetime] = None
    ) -> bool:
        """Determines if a candidate preference score exceeds the stabilization threshold."""
        score = scorer.compute_score(candidate, observations, current_time=current_time)
        return score >= self.stabilization_threshold


class PreferenceResolver:
    """Resolves the preferred option for a category, supporting both async and sync retrieval."""

    def __init__(self, memory_service: Any) -> None:
        self.memory_service = memory_service

    async def resolve_preference(
        self,
        user_id: int,
        category: str,
        context: Optional[AssistantContext] = None
    ) -> Optional[ResolvedPreference]:
        """Asynchronously resolves the preference for a category."""
        # Query memory service for resolved preferences
        resolved_prefs = await self.memory_service.get_resolved_preferences(user_id)
        if category in resolved_prefs:
            val = resolved_prefs[category]
            entry = await self.memory_service.get_preference_by_key(user_id, category)
            score = 1.0
            source = "explicit_override"
            meta = {}
            if entry and entry.metadata and entry.metadata.additional_info:
                score = entry.metadata.additional_info.get("confidence_score", 1.0)
                source = entry.metadata.additional_info.get("source", "learned_stable")
                meta = entry.metadata.additional_info.get("metadata", {})
            return ResolvedPreference(
                user_id=user_id,
                category=category,
                value=val,
                confidence_score=score,
                resolved_at=entry.metadata.created_at if entry else datetime.now(timezone.utc),
                source=source,
                metadata=meta
            )
        
        # System defaults fallback
        SYSTEM_DEFAULTS = {
            "Browser": "Chrome",
            "IDE": "VS Code",
            "Shell": "PowerShell"
        }
        if category in SYSTEM_DEFAULTS:
            return ResolvedPreference(
                user_id=user_id,
                category=category,
                value=SYSTEM_DEFAULTS[category],
                confidence_score=0.5,
                resolved_at=datetime.now(timezone.utc),
                source="default_fallback"
            )
        return None

    def resolve_preference_sync(
        self,
        user_id: int,
        category: str,
        context: Optional[AssistantContext] = None
    ) -> Optional[str]:
        """Synchronously resolves a preference value using pre-loaded context or defaults."""
        SYSTEM_DEFAULTS = {
            "Browser": "Chrome",
            "IDE": "VS Code",
            "Shell": "PowerShell"
        }
        if context:
            resolved_prefs = getattr(context, "resolved_preferences", {}) or {}
            if not resolved_prefs and context.metadata:
                resolved_prefs = context.metadata.get("resolved_preferences", {})
            if category in resolved_prefs:
                return resolved_prefs[category]

        if context and context.preferences:
            for entry in context.preferences:
                if entry.id == category:
                    val = entry.metadata.additional_info.get("value") if entry.metadata.additional_info else None
                    return val if val is not None else entry.content

        return SYSTEM_DEFAULTS.get(category)


class PreferenceConflictResolver:
    """Resolves overlapping or contradictory preferences using scores and timelines."""

    def resolve_conflict(
        self, 
        candidates: List[ResolvedPreference]
    ) -> ResolvedPreference:
        """Selects the leading preference based on confidence score, with timestamp tie-breakers."""
        if not candidates:
            raise ValueError("No preferences to resolve")

        # Sort candidates deterministically:
        # 1. confidence_score (descending)
        # 2. source == 'explicit_override' (True/explicit first, descending)
        # 3. resolved_at timestamp (descending)
        # 4. string representation of value (ascending, deterministic tie-breaker)
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (
                -x.confidence_score,
                -int(x.source == "explicit_override"),
                -x.resolved_at.timestamp(),
                str(x.value)
            )
        )
        return sorted_candidates[0]


class PreferenceLearningCoordinator:
    """Subsystem orchestrator coordinating the learning pipeline."""

    def __init__(
        self,
        learner: PreferenceLearner,
        scorer: PreferenceScorer,
        conflict_resolver: PreferenceConflictResolver,
        memory_service: Any
    ) -> None:
        self.learner = learner
        self.scorer = scorer
        self.conflict_resolver = conflict_resolver
        self.memory_service = memory_service

    def _parse_observation_from_activity(self, user_id: int, entry: MemoryEntry) -> Optional[PreferenceObservation]:
        """Tries to extract a PreferenceObservation from a MemoryEntry activity log."""
        if not entry or entry.memory_type != MemoryType.ACTIVITY:
            return None

        info = entry.metadata.additional_info or {}
        
        # Check if direct observation is stored in additional_info
        obs_data = info.get("preference_observation")
        if isinstance(obs_data, dict):
            try:
                return PreferenceObservation(
                    user_id=user_id,
                    category=obs_data.get("category"),
                    value=obs_data.get("value"),
                    timestamp=entry.metadata.created_at,
                    is_override=obs_data.get("is_override", False),
                    execution_id=entry.id.replace("_activity", ""),
                    execution_status=info.get("status", "SUCCESS"),
                    context_metadata=info.get("input_parameters", {})
                )
            except Exception:
                pass

        # Parse from action/parameters heuristics
        action = str(entry.id).lower()
        params = info.get("input_parameters") or {}
        params_str = str(params).lower()
        status = info.get("status", "SUCCESS")

        category = None
        value = None

        # Check shell
        if any(x in action or x in params_str for x in ["shell", "terminal", "powershell", "pwsh", "bash", "zsh", "cmd"]):
            category = "Shell"
            if "powershell" in params_str or "powershell" in action or "pwsh" in params_str or "pwsh" in action:
                value = "PowerShell"
            elif "bash" in params_str or "bash" in action:
                value = "Bash"
            elif "zsh" in params_str or "zsh" in action:
                value = "Zsh"
            elif "cmd" in params_str or "cmd" in action:
                value = "CMD"
        # Check browser
        elif any(x in action or x in params_str for x in ["browser", "chrome", "firefox", "safari", "edge"]):
            category = "Browser"
            if "chrome" in params_str or "chrome" in action:
                value = "Chrome"
            elif "firefox" in params_str or "firefox" in action:
                value = "Firefox"
            elif "safari" in params_str or "safari" in action:
                value = "Safari"
            elif "edge" in params_str or "edge" in action:
                value = "Edge"
        # Check IDE
        elif any(x in action or x in params_str for x in ["ide", "editor", "vscode", "vs code", "pycharm", "sublime"]):
            category = "IDE"
            if "vscode" in params_str or "vs code" in params_str or "vscode" in action or "vs code" in action:
                value = "VS Code"
            elif "pycharm" in params_str or "pycharm" in action:
                value = "PyCharm"
            elif "sublime" in params_str or "sublime" in action:
                value = "Sublime Text"

        if category and value:
            return PreferenceObservation(
                user_id=user_id,
                category=category,
                value=value,
                timestamp=entry.metadata.created_at,
                is_override=False,
                execution_id=entry.id.replace("_activity", ""),
                execution_status=status,
                context_metadata=params
            )

        return None

    async def process_new_execution(self, user_id: int, execution_id: str) -> None:
        """Triggered upon execution completion. Pulls execution history, processes and saves preferences."""
        logger.info("Preference Learning Started", extra={"user_id": user_id, "execution_id": execution_id})

        # 1. Attempt to retrieve specific execution
        execution_entry = await self.memory_service.get(execution_id + "_activity")
        new_obs = None
        if execution_entry:
            new_obs = self._parse_observation_from_activity(user_id, execution_entry)

        # 2. Get successful executions to form recent observations history
        successful_entries = await self.memory_service.get_successful_executions(limit=100)
        
        observations = []
        for entry in successful_entries:
            obs = self._parse_observation_from_activity(user_id, entry)
            if obs:
                observations.append(obs)

        # Ensure new_obs is represented in the list
        if new_obs:
            if not any(o.execution_id == new_obs.execution_id for o in observations):
                observations.append(new_obs)

        if not observations:
            logger.info("Preference Learning Completed", extra={"user_id": user_id})
            return

        # 3. Extract candidates
        candidates = self.learner.extract_candidates(observations)
        logger.info("Candidates Generated", extra={"count": len(candidates)})

        # 4. Evaluate candidates stability
        stable_by_category: Dict[str, List[ResolvedPreference]] = {}
        for cand in candidates:
            cand_obs = [o for o in observations if o.category == cand.category]
            score = self.scorer.compute_score(cand, cand_obs)
            logger.info("Candidate Score Computed", extra={"category": cand.category, "value": cand.value, "score": score})

            is_stable = self.learner.evaluate_stability(cand, self.scorer, cand_obs)
            if is_stable:
                logger.info("Stable Preference Learned", extra={"category": cand.category, "value": cand.value})
                resolved = ResolvedPreference(
                    user_id=user_id,
                    category=cand.category,
                    value=cand.value,
                    confidence_score=score,
                    resolved_at=cand.last_observed,
                    source="explicit_override" if cand.is_explicit else "learned_stable",
                    metadata={
                        "observation_count": cand.observation_count,
                        "success_count": cand.success_count,
                    }
                )
                if cand.category not in stable_by_category:
                    stable_by_category[cand.category] = []
                stable_by_category[cand.category].append(resolved)

        # 5. Resolve conflicts and save stable preferences
        for category, resolved_list in stable_by_category.items():
            if not resolved_list:
                continue

            resolved_pref = resolved_list[0]
            if len(resolved_list) > 1:
                resolved_pref = self.conflict_resolver.resolve_conflict(resolved_list)
                logger.info("Conflict Resolved", extra={"category": category, "resolved_value": resolved_pref.value})

            # Check if we should overwrite existing preference
            existing_entry = await self.memory_service.get_preference_by_key(user_id, category)
            should_save = True
            if existing_entry:
                try:
                    existing_source = existing_entry.metadata.additional_info.get("source")
                    existing_score = existing_entry.metadata.additional_info.get("confidence_score", 0.0)
                    
                    if existing_source == "explicit_override" and resolved_pref.source != "explicit_override":
                        should_save = False
                    elif (resolved_pref.source == existing_source or resolved_pref.source != "explicit_override") and existing_score >= resolved_pref.confidence_score:
                        existing_val = existing_entry.metadata.additional_info.get("value")
                        if str(existing_val).lower() == str(resolved_pref.value).lower():
                            should_save = False
                except Exception:
                    pass

            if should_save:
                pref_entry = MemoryEntry(
                    id=category,
                    content=str(resolved_pref.value),
                    memory_type=MemoryType.PREFERENCE,
                    metadata=MemoryMetadata(
                        created_at=resolved_pref.resolved_at,
                        updated_at=datetime.now(timezone.utc),
                        additional_info={
                            "user_id": user_id,
                            "value": resolved_pref.value,
                            "confidence_score": resolved_pref.confidence_score,
                            "source": resolved_pref.source,
                            "metadata": resolved_pref.metadata,
                        }
                    )
                )
                await self.memory_service.save(pref_entry)
                logger.info("Preference Saved", extra={"category": category, "value": resolved_pref.value})

        logger.info("Preference Learning Completed", extra={"user_id": user_id})

    async def register_manual_override(
        self, 
        user_id: int, 
        category: str, 
        value: Any
    ) -> ResolvedPreference:
        """Forcibly overrides a preference based on direct user correction."""
        logger.info("Preference Learning Started", extra={"user_id": user_id, "override": category})

        resolved = ResolvedPreference(
            user_id=user_id,
            category=category,
            value=value,
            confidence_score=1.0,
            resolved_at=datetime.now(timezone.utc),
            source="explicit_override",
            metadata={"manual_override": True}
        )

        pref_entry = MemoryEntry(
            id=category,
            content=str(value),
            memory_type=MemoryType.PREFERENCE,
            metadata=MemoryMetadata(
                created_at=resolved.resolved_at,
                updated_at=resolved.resolved_at,
                additional_info={
                    "user_id": user_id,
                    "value": value,
                    "confidence_score": 1.0,
                    "source": "explicit_override",
                    "metadata": resolved.metadata,
                }
            )
        )
        await self.memory_service.save(pref_entry)

        logger.info("Stable Preference Learned", extra={"category": category, "value": value})
        logger.info("Preference Saved", extra={"category": category, "value": value})
        logger.info("Preference Learning Completed", extra={"user_id": user_id})

        return resolved
