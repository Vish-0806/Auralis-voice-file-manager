"""Abstract Base Class interfaces for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Defines canonical interfaces for checkpoint manager, state store, recovery engine, rollback manager, provider, and runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.recovery.recovery_models import (
    CheckpointType,
    ExecutionCheckpoint,
    RecoveryExecution,
    RecoveryHealth,
    RecoveryPlan,
    RecoveryStatistics,
    RecoveryStrategy,
    RollbackExecution,
    RollbackPlan,
    SnapshotType,
    StateSnapshot,
)


class ICheckpointManager(ABC):
    """Interface for managing execution checkpoints."""

    @abstractmethod
    def create_checkpoint(
        self,
        execution_id: str,
        checkpoint_type: CheckpointType,
        state_data: Dict[str, Any],
        step_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCheckpoint:
        """Create and store execution checkpoint."""
        pass

    @abstractmethod
    def get_latest_checkpoint(self, execution_id: str) -> Optional[ExecutionCheckpoint]:
        """Fetch latest checkpoint for execution_id."""
        pass

    @abstractmethod
    def list_checkpoints(self, execution_id: str) -> List[ExecutionCheckpoint]:
        """List all checkpoints for execution_id."""
        pass


class IStateStore(ABC):
    """Interface for managing execution state snapshots."""

    @abstractmethod
    def save_snapshot(
        self,
        execution_id: str,
        context_data: Dict[str, Any],
        snapshot_type: SnapshotType = SnapshotType.FULL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateSnapshot:
        """Save a state snapshot."""
        pass

    @abstractmethod
    def get_latest_snapshot(self, execution_id: str) -> Optional[StateSnapshot]:
        """Get latest snapshot for execution_id."""
        pass


class IRecoveryEngine(ABC):
    """Interface for planning and executing recovery strategies."""

    @abstractmethod
    def plan_recovery(
        self,
        execution_id: str,
        strategy: RecoveryStrategy,
        target_checkpoint_id: Optional[str] = None,
    ) -> RecoveryPlan:
        """Generate recovery plan."""
        pass

    @abstractmethod
    def execute_recovery(self, plan: RecoveryPlan) -> RecoveryExecution:
        """Execute recovery plan."""
        pass


class IRollbackManager(ABC):
    """Interface for planning and executing step rollback operations."""

    @abstractmethod
    def plan_rollback(
        self,
        execution_id: str,
        target_checkpoint_id: str,
        rollback_steps: Optional[List[str]] = None,
    ) -> RollbackPlan:
        """Generate rollback plan."""
        pass

    @abstractmethod
    def execute_rollback(self, plan: RollbackPlan) -> RollbackExecution:
        """Execute rollback plan."""
        pass


class IRecoveryProvider(ABC):
    """Interface for aggregate Recovery Provider."""

    @abstractmethod
    def create_checkpoint(
        self,
        execution_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
        step_index: int = 0,
    ) -> ExecutionCheckpoint:
        """Create execution checkpoint."""
        pass

    @abstractmethod
    def recover_execution(
        self,
        execution_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RESUME_CHECKPOINT,
    ) -> RecoveryExecution:
        """Recover failed execution."""
        pass

    @abstractmethod
    def rollback_execution(
        self,
        execution_id: str,
        target_checkpoint_id: str,
    ) -> RollbackExecution:
        """Rollback execution state to checkpoint."""
        pass

    @abstractmethod
    def health_check(self) -> RecoveryHealth:
        """Report component health statuses."""
        pass

    @abstractmethod
    def get_statistics(self) -> RecoveryStatistics:
        """Return snapshot of aggregate recovery statistics."""
        pass


class IRecoveryRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize recovery runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down recovery runtime lifecycle."""
        pass

    @abstractmethod
    def health_check(self) -> RecoveryHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> RecoveryStatistics:
        """Fetch snapshot of recovery statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset recovery statistics and transient state."""
        pass
