"""Assistant Memory Provider implementation for Auralis (Phase 13.5).

Aggregates AssistantContextManager, PreferenceManager, and MemoryCoordinator into a unified provider.
Exposes health diagnostics, performance statistics, and capabilities using constructor dependency injection only.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.memory.assistant_context_manager import AssistantContextManager
from brain.assistant.memory.interfaces import (
    IAssistantContextManager,
    IAssistantMemoryCoordinator,
    IAssistantMemoryProvider,
    IAssistantPreferenceManager,
)
from brain.assistant.memory.memory_coordinator import MemoryCoordinator
from brain.assistant.memory.models import (
    AssistantMemoryHealth,
    AssistantMemorySnapshot,
    AssistantMemoryStatistics,
    AssistantWorkingContext,
)
from brain.assistant.memory.preference_manager import PreferenceManager

logger = logging.getLogger(__name__)


class AssistantMemoryProvider(IAssistantMemoryProvider):
    """Aggregating provider for assistant context merging, preferences, and multi-subsystem memory coordination."""

    def __init__(
        self,
        context_manager: Optional[IAssistantContextManager] = None,
        preference_manager: Optional[IAssistantPreferenceManager] = None,
        coordinator: Optional[IAssistantMemoryCoordinator] = None,
    ) -> None:
        """Initializes AssistantMemoryProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._context_manager = context_manager or AssistantContextManager(lock=self._lock)
        self._preference_manager = preference_manager or PreferenceManager(lock=self._lock)
        self._coordinator = coordinator or MemoryCoordinator(
            context_manager=self._context_manager,  # type: ignore[arg-type]
            lock=self._lock,
        )

        self._initialized = False
        self._start_time: Optional[float] = None

        # Statistics metrics
        self._total_merges = 0
        self._total_snapshots = 0
        self._total_latency_ms = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def context_manager(self) -> IAssistantContextManager:
        with self._lock:
            return self._context_manager

    @property
    def preference_manager(self) -> IAssistantPreferenceManager:
        with self._lock:
            return self._preference_manager

    @property
    def coordinator(self) -> IAssistantMemoryCoordinator:
        with self._lock:
            return self._coordinator

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def create_snapshot(
        self,
        session_id: Optional[str] = None,
        conversation_runtime: Optional[Any] = None,
        dialogue_runtime: Optional[Any] = None,
        decision_runtime: Optional[Any] = None,
        execution_runtime: Optional[Any] = None,
        ai_memory_runtime: Optional[Any] = None,
        token_budget: int = 4096,
    ) -> AssistantMemorySnapshot:
        """Create snapshot through coordinator while recording diagnostic metrics."""
        t0 = time.time()
        snapshot = self._coordinator.create_snapshot(
            session_id=session_id,
            conversation_runtime=conversation_runtime,
            dialogue_runtime=dialogue_runtime,
            decision_runtime=decision_runtime,
            execution_runtime=execution_runtime,
            ai_memory_runtime=ai_memory_runtime,
            token_budget=token_budget,
        )
        latency = (time.time() - t0) * 1000.0

        with self._lock:
            self._total_snapshots += 1
            self._total_merges += 1
            self._total_latency_ms += latency

        return snapshot

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("AssistantMemoryProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("AssistantMemoryProvider shutdown complete")

    def clear(self) -> None:
        """Reset provider statistics and sub-managers."""
        with self._lock:
            self._total_merges = 0
            self._total_snapshots = 0
            self._total_latency_ms = 0.0
            if hasattr(self._preference_manager, "clear"):
                self._preference_manager.clear()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_health(self) -> AssistantMemoryHealth:
        """Expose real-time diagnostic health snapshot."""
        with self._lock:
            subsystems = {
                "context_manager": self._context_manager is not None,
                "preference_manager": self._preference_manager is not None,
                "coordinator": self._coordinator is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("AssistantMemoryProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return AssistantMemoryHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> AssistantMemoryStatistics:
        """Expose aggregated memory integration performance metrics."""
        with self._lock:
            avg_latency = (self._total_latency_ms / self._total_merges) if self._total_merges > 0 else 0.0

            dups = 0
            trims = 0
            if hasattr(self._context_manager, "duplicates_removed_count"):
                dups = getattr(self._context_manager, "duplicates_removed_count")
            if hasattr(self._context_manager, "trims_count"):
                trims = getattr(self._context_manager, "trims_count")

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return AssistantMemoryStatistics(
                total_context_merges=self._total_merges,
                total_snapshots_generated=self._total_snapshots,
                preferences_merged=0,
                duplicates_removed=dups,
                token_budget_trims=trims,
                average_merge_latency_ms=avg_latency,
                uptime_seconds=uptime,
                metadata={},
            )
