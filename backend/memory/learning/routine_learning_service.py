"""Routine Learning Service public interface module."""

import logging
from typing import Any, Dict, List, Optional

from memory.models.domain_models import ExecutionHistoryDomain, RoutineLearningDomain
from memory.learning.learning_models import RoutineSuggestion
from memory.learning.routine_learning_engine import RoutineLearningEngine
from memory.learning.learning_scheduler import LearningScheduler

logger = logging.getLogger(__name__)


class RoutineLearningService:
    """Sole public gateway/API for all user Routine Learning operations in Auralis."""

    def __init__(self, engine: Optional[RoutineLearningEngine] = None) -> None:
        """Initializes the RoutineLearningService.

        If engine is omitted, resolves dependencies dynamically via SessionLocal,
        RoutineRepository, and ExecutionRepository.

        Args:
            engine: Optional custom RoutineLearningEngine instance.
        """
        if engine is not None:
            self._engine = engine
        else:
            from memory.database.session import SessionLocal
            from memory.repository.routine_repository import RoutineRepository
            from memory.repository.execution_repository import ExecutionRepository

            self._db = SessionLocal()
            routine_repo = RoutineRepository(self._db)
            exec_repo = ExecutionRepository(self._db)
            self._engine = RoutineLearningEngine(
                routine_repository=routine_repo,
                execution_repository=exec_repo,
            )

        self._scheduler: Optional[LearningScheduler] = None

    def __del__(self) -> None:
        """Ensures the scheduler is stopped and DB session closed on garbage collection."""
        if hasattr(self, "_scheduler") and self._scheduler is not None:
            try:
                self._scheduler.stop()
            except Exception:
                pass
        if hasattr(self, "_db"):
            try:
                self._db.close()
            except Exception:
                pass

    def record(
        self,
        user_id: int,
        action: str,
        input_parameters: Dict[str, Any],
        status: str,
        duration_ms: Optional[int] = None,
        logs: Optional[str] = None,
    ) -> ExecutionHistoryDomain:
        """Records a user action execution event log.

        Args:
            user_id: Owner user identifier.
            action: Capability action name.
            input_parameters: Config options passed to the run.
            status: Success/failure status.
            duration_ms: Total action time duration.
            logs: Output prints or stack trace.

        Returns:
            The saved ExecutionHistoryDomain object.
        """
        return self._engine.record_execution(
            user_id=user_id,
            action=action,
            input_parameters=input_parameters,
            status=status,
            duration_ms=duration_ms,
            logs=logs,
        )

    def analyze(self, user_id: int, min_confidence: float = 0.3) -> List[RoutineSuggestion]:
        """Runs the pattern analyzer to detect recurring routines.

        Args:
            user_id: Owner user identifier.
            min_confidence: Confidence threshold floor (e.g. 0.3).

        Returns:
            List of generated RoutineSuggestion objects.
        """
        return self._engine.analyze_execution_history(user_id, min_confidence)

    def accept(self, user_id: int, suggestion: RoutineSuggestion) -> RoutineLearningDomain:
        """Accepts a suggestion, saving it to active routines list.

        Args:
            user_id: Owner user identifier.
            suggestion: The RoutineSuggestion object to confirm.

        Returns:
            The created RoutineLearningDomain object.
        """
        return self._engine.accept_suggestion(user_id, suggestion)

    def reject(self, user_id: int, trigger_event: str) -> None:
        """Rejects/mutes a suggested trigger event.

        Args:
            user_id: Owner user identifier.
            trigger_event: Trigger description string.
        """
        self._engine.reject_suggestion(user_id, trigger_event)

    def delete(self, user_id: int, routine_id: int) -> bool:
        """Deletes a saved routine by ID.

        Args:
            user_id: Owner user identifier.
            routine_id: Routine primary identifier.

        Returns:
            True if deleted, False if not found.
        """
        return self._engine.delete_routine(user_id, routine_id)

    def list(self, user_id: int) -> List[RoutineLearningDomain]:
        """Lists active learned routines.

        Args:
            user_id: Owner user identifier.

        Returns:
            List of RoutineLearningDomain objects.
        """
        return self._engine.list_routines(user_id)

    def start_scheduler(self, user_id: int, interval_seconds: float = 3600.0) -> None:
        """Starts background execution for recurring patterns analyzer checks.

        Args:
            user_id: Owner user identifier to run against.
            interval_seconds: Run scheduler check frequency.
        """
        if self._scheduler is not None:
            self._scheduler.stop()

        def _periodic_check() -> None:
            suggs = self.analyze(user_id)
            if suggs:
                logger.info(f"Periodic analyzer found {len(suggs)} routine suggestions for user {user_id}.")

        self._scheduler = LearningScheduler(callback=_periodic_check, interval_seconds=interval_seconds)
        self._scheduler.start()

    def stop_scheduler(self) -> None:
        """Halts the periodic scheduler if active."""
        if self._scheduler is not None:
            self._scheduler.stop()
            self._scheduler = None
