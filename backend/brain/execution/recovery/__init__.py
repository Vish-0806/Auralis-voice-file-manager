"""Execution Recovery & State Management Runtime package for Auralis (Phase 12.8).

Exports domain models, enums, exceptions, interfaces, checkpoint manager, state store,
recovery engine, rollback manager, provider, runtime lifecycle manager, and global singleton accessors.
"""

from .checkpoint_manager import CheckpointManager
from .exceptions import (
    CheckpointError,
    RecoveryException,
    RecoveryExecutionError,
    RollbackError,
    StateStoreError,
)

from .interfaces import (
    ICheckpointManager,
    IRecoveryEngine,
    IRecoveryProvider,
    IRecoveryRuntime,
    IRollbackManager,
    IStateStore,
)
from .recovery_engine import RecoveryEngine
from .recovery_models import (
    CheckpointType,
    ExecutionCheckpoint,
    ExecutionState,
    RecoveryExecution,
    RecoveryHealth,
    RecoveryPlan,
    RecoveryStatistics,
    RecoveryStatus,
    RecoveryStrategy,
    RollbackExecution,
    RollbackPlan,
    RollbackStatus,
    SnapshotType,
    StateSnapshot,
)
from .recovery_provider import RecoveryProvider
from .recovery_runtime import RecoveryRuntime, RecoveryRuntimeStatus
from .rollback_manager import RollbackManager
from .runtime import get_recovery_runtime, reset_recovery_runtime
from .state_store import StateStore

__all__ = [
    # Enums & Models
    "CheckpointType",
    "ExecutionState",
    "RecoveryStatus",
    "RecoveryStrategy",
    "RollbackStatus",
    "SnapshotType",
    "ExecutionCheckpoint",
    "StateSnapshot",
    "RecoveryPlan",
    "RecoveryExecution",
    "RollbackPlan",
    "RollbackExecution",
    "RecoveryStatistics",
    "RecoveryHealth",
    # Exceptions
    "RecoveryException",
    "CheckpointError",
    "StateStoreError",
    "RecoveryExecutionError",
    "RollbackError",
    # Interfaces
    "ICheckpointManager",
    "IStateStore",
    "IRecoveryEngine",
    "IRollbackManager",
    "IRecoveryProvider",
    "IRecoveryRuntime",
    # Core Components
    "CheckpointManager",
    "StateStore",
    "RecoveryEngine",
    "RollbackManager",
    "RecoveryProvider",
    "RecoveryRuntime",
    "RecoveryRuntimeStatus",
    # Global Accessors
    "get_recovery_runtime",
    "reset_recovery_runtime",
]
