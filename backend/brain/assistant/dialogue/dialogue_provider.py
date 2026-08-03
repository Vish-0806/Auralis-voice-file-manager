"""Dialogue Provider implementation for Auralis (Phase 13.3).

Aggregates DialogueManager, PolicyManager, and StateManager into a unified dialogue subsystem.
Exposes health diagnostic reports, statistics metrics, and capabilities using constructor dependency injection only.
"""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from brain.assistant.dialogue.dialogue_manager import DialogueManager
from brain.assistant.dialogue.interfaces import (
    IDialogueManager,
    IDialoguePolicyManager,
    IDialogueProvider,
    IDialogueStateManager,
)
from brain.assistant.dialogue.models import (
    DialogueHealth,
    DialogueStatistics,
    DialogueStatus,
)
from brain.assistant.dialogue.policy_manager import PolicyManager
from brain.assistant.dialogue.state_manager import StateManager

logger = logging.getLogger(__name__)


class DialogueProvider(IDialogueProvider):
    """Aggregating provider uniting dialogue session management, policy evaluation, and state tracking."""

    def __init__(
        self,
        manager: Optional[IDialogueManager] = None,
        policy_manager: Optional[IDialoguePolicyManager] = None,
        state_manager: Optional[IDialogueStateManager] = None,
    ) -> None:
        """Initializes DialogueProvider using constructor dependency injection only."""
        self._lock = threading.RLock()
        self._manager = manager or DialogueManager(lock=self._lock)
        self._policy_manager = policy_manager or PolicyManager(lock=self._lock)
        self._state_manager = state_manager or StateManager(lock=self._lock)

        self._initialized = False
        self._start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def manager(self) -> IDialogueManager:
        with self._lock:
            return self._manager

    @property
    def policy_manager(self) -> IDialoguePolicyManager:
        with self._lock:
            return self._policy_manager

    @property
    def state_manager(self) -> IDialogueStateManager:
        with self._lock:
            return self._state_manager

    @property
    def is_initialized(self) -> bool:
        with self._lock:
            return self._initialized

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize dialogue provider resources."""
        with self._lock:
            if self._initialized:
                return

            self._initialized = True
            self._start_time = time.time()
            logger.info("DialogueProvider initialized successfully")

    def shutdown(self) -> None:
        """Gracefully shut down dialogue provider resources."""
        with self._lock:
            if not self._initialized:
                return

            self._initialized = False
            self._start_time = None
            logger.info("DialogueProvider shutdown complete")

    def clear(self) -> None:
        """Reset dialogue state, manager sessions, and metrics."""
        with self._lock:
            if hasattr(self._manager, "clear"):
                self._manager.clear()  # type: ignore[union-attr]
            if hasattr(self._state_manager, "clear"):
                self._state_manager.clear()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Health & Statistics
    # ------------------------------------------------------------------

    def get_health(self) -> DialogueHealth:
        """Expose real-time diagnostic health snapshot."""
        with self._lock:
            subsystems = {
                "manager": self._manager is not None,
                "policy_manager": self._policy_manager is not None,
                "state_manager": self._state_manager is not None,
            }
            issues: List[str] = []
            if not self._initialized:
                issues.append("DialogueProvider is not initialized")

            healthy = self._initialized and len(issues) == 0

            return DialogueHealth(
                status="READY" if healthy else ("UNINITIALIZED" if not self._initialized else "DEGRADED"),
                healthy=healthy,
                subsystems=subsystems,
                statistics=self.get_statistics().model_dump(),
                detected_issues=issues,
                checked_at=datetime.now(timezone.utc),
                metadata={},
            )

    def get_statistics(self) -> DialogueStatistics:
        """Expose aggregated statistics across all dialogue sessions and turns."""
        with self._lock:
            all_sessions = self._manager.list_sessions() if self._manager else []
            total_created = len(all_sessions)
            active_count = len([s for s in all_sessions if s.status in (DialogueStatus.IDLE, DialogueStatus.PROCESSING, DialogueStatus.LISTENING, DialogueStatus.RESPONDING)])
            total_turns = sum(len(s.turns) for s in all_sessions)

            clarifications = 0
            confirmations = 0
            for s in all_sessions:
                for t in s.turns:
                    if t.requires_clarification:
                        clarifications += 1
                    if t.requires_confirmation:
                        confirmations += 1

            avg_turns = (total_turns / total_created) if total_created > 0 else 0.0

            uptime = 0.0
            if self._start_time is not None and self._initialized:
                uptime = max(0.0, time.time() - self._start_time)

            return DialogueStatistics(
                total_sessions_created=total_created,
                active_sessions=active_count,
                total_turns_processed=total_turns,
                clarifications_requested=clarifications,
                confirmations_requested=confirmations,
                average_turns_per_session=avg_turns,
                uptime_seconds=uptime,
                metadata={},
            )
