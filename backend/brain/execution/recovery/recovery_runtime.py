"""Recovery Runtime for the Auralis Execution Recovery & State Management Runtime (Phase 12.8).

Thread-safe singleton lifecycle manager orchestrating the RecoveryProvider.
Manages status transitions, checkpoint/recovery/rollback delegation, health monitoring, and statistics.
"""

from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.execution.recovery.interfaces import IRecoveryRuntime
from brain.execution.recovery.recovery_models import (
    CheckpointType,
    ExecutionCheckpoint,
    RecoveryExecution,
    RecoveryHealth,
    RecoveryStatistics,
    RecoveryStrategy,
    RollbackExecution,
    StateSnapshot,
)
from brain.execution.recovery.recovery_provider import RecoveryProvider

logger = logging.getLogger(__name__)


class RecoveryRuntimeStatus(str, Enum):
    """Lifecycle status states for the Execution Recovery Runtime."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RECOVERING = "RECOVERING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class RecoveryRuntime(IRecoveryRuntime):
    """Thread-safe singleton runtime managing the RecoveryProvider lifecycle."""

    def __init__(self, provider: Optional[RecoveryProvider] = None) -> None:
        """Initializes RecoveryRuntime with optional provider instance."""
        self._lock = threading.RLock()
        self._status = RecoveryRuntimeStatus.INITIALIZING
        self._provider = provider or RecoveryProvider()

    @property
    def status(self) -> RecoveryRuntimeStatus:
        with self._lock:
            return self._status

    @property
    def provider(self) -> RecoveryProvider:
        return self._provider

    def initialize(self) -> bool:
        """Initialize the Execution Recovery Runtime.

        Returns:
            True if initialized successfully.
        """
        with self._lock:
            if self._status == RecoveryRuntimeStatus.READY:
                return True

            try:
                self._status = RecoveryRuntimeStatus.READY
                logger.info("Execution Recovery Runtime Initialized")
                return True
            except Exception as exc:
                self._status = RecoveryRuntimeStatus.ERROR
                logger.error("RecoveryRuntime initialization failed: %s", exc)
                return False

    def shutdown(self) -> bool:
        """Gracefully shut down recovery runtime.

        Returns:
            True always.
        """
        with self._lock:
            self._status = RecoveryRuntimeStatus.SHUTDOWN
            logger.info("Execution Recovery Runtime Shutdown")
            return True

    def create_checkpoint(
        self,
        execution_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTOMATIC,
        step_index: int = 0,
    ) -> ExecutionCheckpoint:
        """Create execution checkpoint through provider."""
        with self._lock:
            if self._status in (RecoveryRuntimeStatus.INITIALIZING, RecoveryRuntimeStatus.SHUTDOWN):
                self.initialize()

        return self._provider.create_checkpoint(
            execution_id=execution_id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            step_index=step_index,
        )

    def save_snapshot(
        self,
        execution_id: str,
        context_data: Dict[str, Any],
    ) -> StateSnapshot:
        """Save state snapshot through provider."""
        with self._lock:
            if self._status in (RecoveryRuntimeStatus.INITIALIZING, RecoveryRuntimeStatus.SHUTDOWN):
                self.initialize()

        return self._provider.save_snapshot(
            execution_id=execution_id,
            context_data=context_data,
        )

    def recover_execution(
        self,
        execution_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RESUME_CHECKPOINT,
    ) -> RecoveryExecution:
        """Recover execution through provider."""
        with self._lock:
            if self._status in (RecoveryRuntimeStatus.INITIALIZING, RecoveryRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = RecoveryRuntimeStatus.RECOVERING

        try:
            return self._provider.recover_execution(
                execution_id=execution_id,
                strategy=strategy,
            )
        finally:
            with self._lock:
                if self._status == RecoveryRuntimeStatus.RECOVERING:
                    self._status = prev_status if prev_status != RecoveryRuntimeStatus.INITIALIZING else RecoveryRuntimeStatus.READY

    def rollback_execution(
        self,
        execution_id: str,
        target_checkpoint_id: str,
    ) -> RollbackExecution:
        """Rollback execution state through provider."""
        with self._lock:
            if self._status in (RecoveryRuntimeStatus.INITIALIZING, RecoveryRuntimeStatus.SHUTDOWN):
                self.initialize()

            prev_status = self._status
            self._status = RecoveryRuntimeStatus.RECOVERING

        try:
            return self._provider.rollback_execution(
                execution_id=execution_id,
                target_checkpoint_id=target_checkpoint_id,
            )
        finally:
            with self._lock:
                if self._status == RecoveryRuntimeStatus.RECOVERING:
                    self._status = prev_status if prev_status != RecoveryRuntimeStatus.INITIALIZING else RecoveryRuntimeStatus.READY

    def health_check(self) -> RecoveryHealth:
        """Fetch health check diagnostic status."""
        with self._lock:
            provider_health = self._provider.health_check()
            is_healthy = (self._status in (RecoveryRuntimeStatus.READY, RecoveryRuntimeStatus.RECOVERING)) and provider_health.healthy

            issues = list(provider_health.detected_issues)
            if self._status == RecoveryRuntimeStatus.ERROR:
                issues.append("Recovery runtime is in ERROR status")

            return RecoveryHealth(
                status=self._status.value if is_healthy else "ERROR",
                healthy=is_healthy,
                components=provider_health.components,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                metadata={"thread_safety": "PROTECTED"},
            )

    def get_statistics(self) -> RecoveryStatistics:
        """Fetch recovery statistics snapshot."""
        with self._lock:
            return self._provider.get_statistics()

    def clear(self) -> None:
        """Reset recovery statistics and transient state."""
        with self._lock:
            self._provider.clear()
            if self._status != RecoveryRuntimeStatus.SHUTDOWN:
                self._status = RecoveryRuntimeStatus.READY
            logger.info("RecoveryRuntime cleared")
