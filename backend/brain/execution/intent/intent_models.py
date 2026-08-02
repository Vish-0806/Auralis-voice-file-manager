"""Domain data models and enumerations for the Auralis Intent Resolution Engine (Phase 12.2).

Defines immutable Pydantic v2 models representing recognized intents, extracted entities,
context, intent candidates, resolutions, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional, Tuple
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class IntentCategory(str, Enum):
    """Enumeration of recognized intent categories."""

    FILE_MANAGEMENT = "FILE_MANAGEMENT"
    FILE_SEARCH = "FILE_SEARCH"
    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    APPLICATION_CONTROL = "APPLICATION_CONTROL"
    WINDOW_MANAGEMENT = "WINDOW_MANAGEMENT"
    WORKFLOW_PLANNING = "WORKFLOW_PLANNING"
    AI_GENERATION = "AI_GENERATION"
    ASSISTANT_QUERY = "ASSISTANT_QUERY"
    DEVICE_CONTROL = "DEVICE_CONTROL"
    CLIPBOARD = "CLIPBOARD"
    SCREENSHOT = "SCREENSHOT"
    UNKNOWN = "UNKNOWN"


class IntentConfidence(str, Enum):
    """Confidence ratings for intent recognition."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class ResolutionStatus(str, Enum):
    """Status outcomes for intent resolution."""

    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    INVALID = "INVALID"
    FAILED = "FAILED"


class EntityType(str, Enum):
    """Types of extracted command entities."""

    FILE = "FILE"
    FOLDER = "FOLDER"
    APPLICATION = "APPLICATION"
    PATH = "PATH"
    NUMBER = "NUMBER"
    DATE = "DATE"
    TIME = "TIME"
    WINDOW_NAME = "WINDOW_NAME"
    DEVICE_NAME = "DEVICE_NAME"
    KEYBOARD_SHORTCUT = "KEYBOARD_SHORTCUT"
    UNKNOWN = "UNKNOWN"


class AmbiguityLevel(str, Enum):
    """Classification levels for intent ambiguity."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UserIntent(BaseModel):
    """Immutable model representing a recognized user intent."""

    model_config = ConfigDict(frozen=True)

    intent_id: str = Field(default_factory=lambda: f"intent-{uuid.uuid4().hex[:8]}")
    category: IntentCategory = IntentCategory.UNKNOWN
    raw_prompt: str = ""
    normalized_text: str = ""
    action: str = "UNKNOWN"
    confidence: IntentConfidence = IntentConfidence.NONE
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentEntity(BaseModel):
    """Immutable model representing a structured parameter entity extracted from input."""

    model_config = ConfigDict(frozen=True)

    entity_id: str = Field(default_factory=lambda: f"ent-{uuid.uuid4().hex[:8]}")
    entity_type: EntityType = EntityType.UNKNOWN
    name: str = ""
    value: Any = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    position: Optional[Tuple[int, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentContext(BaseModel):
    """Immutable model encapsulating contextual variables for intent resolution."""

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: f"ctx-{uuid.uuid4().hex[:8]}")
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    workspace_context: Dict[str, Any] = Field(default_factory=dict)
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    resolved_preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentCandidate(BaseModel):
    """Immutable model representing an alternative candidate interpretation."""

    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(default_factory=lambda: f"cand-{uuid.uuid4().hex[:8]}")
    intent: UserIntent = Field(default_factory=UserIntent)
    entities: List[IntentEntity] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""


class IntentResolution(BaseModel):
    """Immutable model representing the final outcome of intent resolution."""

    model_config = ConfigDict(frozen=True)

    resolution_id: str = Field(default_factory=lambda: f"res-{uuid.uuid4().hex[:8]}")
    status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    primary_intent: Optional[UserIntent] = None
    entities: List[IntentEntity] = Field(default_factory=list)
    candidates: List[IntentCandidate] = Field(default_factory=list)
    ambiguity_level: AmbiguityLevel = AmbiguityLevel.NONE
    diagnostics: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResolutionStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Intent Resolution Subsystem."""

    model_config = ConfigDict(frozen=True)

    total_resolutions: int = 0
    resolved_count: int = 0
    ambiguous_count: int = 0
    failed_count: int = 0
    average_resolution_time_ms: float = 0.0
    resolutions_by_category: Dict[str, int] = Field(default_factory=dict)
    active_resolutions: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentHealth(BaseModel):
    """Immutable model representing health status of the Intent Resolution Subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
