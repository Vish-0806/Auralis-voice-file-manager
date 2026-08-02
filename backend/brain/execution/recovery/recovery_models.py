"""Domain data models and enumerations for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Defines immutable Pydantic v2 models representing execution checkpoints, state snapshots,
recovery plans, recovery executions, rollback plans, rollback executions, statistics, and health reports.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class CheckpointType(str, Enum):
    """Types of execution checkpoints."""

    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    STAGE = "STAGE"
    STEP = "STEP"
    EMERGENCY = "EMERGENCY"


class ExecutionState(str, Enum):
    """Operational states for recovery management."""

    IDLE = "IDLE"
    SAVING = "SAVING"
    RECOVERING = "RECOVERING"
    ROLLING_BACK = "ROLLING_BACK"
    RESTORED = "RESTORED"
    FAILED = "FAILED"


class RecoveryStatus(str, Enum):
    """Status states for recovery executions."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class RecoveryStrategy(str, Enum):
    """Strategies for recovering failed execution states."""

    RETRY_STEP = "RETRY_STEP"
    RESUME_CHECKPOINT = "RESUME_CHECKPOINT"
    ROLLBACK_STAGE = "ROLLBACK_STAGE"
    ABORT_EXECUTION = "ABORT_EXECUTION"
    FAILOVER = "FAILOVER"


class RollbackStatus(str, Enum):
    """Status states for rollback operations."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SnapshotType(str, Enum):
    """Types of state snapshots."""

    FULL = "FULL"
    DELTA = "DELTA"
    INCREMENTAL = "INCREMENTAL"


class ExecutionCheckpoint(BaseModel):
    """Immutable model representing an execution checkpoint."""

    model_config = ConfigDict(frozen=True)

    checkpoint_id: str = Field(default_factory=lambda: f"chk-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC
    state_data: Dict[str, Any] = Field(default_factory=dict)
    step_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StateSnapshot(BaseModel):
    """Immutable model representing a context state snapshot."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(default_factory=lambda: f"snap-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    snapshot_type: SnapshotType = SnapshotType.FULL
    context_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryPlan(BaseModel):
    """Immutable model defining steps and target checkpoint for recovery."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(default_factory=lambda: f"rec-plan-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    strategy: RecoveryStrategy = RecoveryStrategy.RESUME_CHECKPOINT
    target_checkpoint_id: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryExecution(BaseModel):
    """Immutable model tracking the outcome of executing a RecoveryPlan."""

    model_config = ConfigDict(frozen=True)

    recovery_id: str = Field(default_factory=lambda: f"rec-exec-{uuid.uuid4().hex[:8]}")
    plan_id: str = ""
    status: RecoveryStatus = RecoveryStatus.SUCCESS
    attempts: int = 1
    error: Optional[str] = None
    restored_state: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class RollbackPlan(BaseModel):
    """Immutable model defining steps to revert execution changes to a checkpoint."""

    model_config = ConfigDict(frozen=True)

    rollback_id: str = Field(default_factory=lambda: f"rb-plan-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    target_checkpoint_id: str = ""
    rollback_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RollbackExecution(BaseModel):
    """Immutable model tracking the outcome of executing a RollbackPlan."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = ""
    rollback_id: str = Field(default_factory=lambda: f"rb-exec-{uuid.uuid4().hex[:8]}")
    status: RollbackStatus = RollbackStatus.COMPLETED
    reverted_steps: int = 0
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecoveryStatistics(BaseModel):
    """Immutable model representing diagnostic statistics of the Recovery subsystem."""

    model_config = ConfigDict(frozen=True)

    total_checkpoints: int = 0
    total_recoveries: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    total_rollbacks: int = 0
    successful_rollbacks: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecoveryHealth(BaseModel):
    """Immutable model representing health status of the Recovery subsystem."""

    model_config = ConfigDict(frozen=True)

    status: str = "READY"
    healthy: bool = True
    components: Dict[str, bool] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    detected_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
