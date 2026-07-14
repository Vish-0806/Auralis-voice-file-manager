"""Routine Learning Engine coordinator."""

import logging
import threading
from typing import Any, Dict, List, Optional, Set

from memory.models.domain_models import ExecutionHistoryDomain, RoutineLearningDomain
from memory.repository.routine_repository import RoutineRepository
from memory.repository.execution_repository import ExecutionRepository
from memory.learning.learning_models import RoutineSuggestion, RoutineNotFoundError, LearningError
from memory.learning.learning_validator import LearningValidator
from memory.learning.pattern_analyzer import PatternAnalyzer
from memory.learning.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)


class RoutineLearningEngine:
    """Orchestrates pattern mining, suggestion creation, and routine persistence."""

    def __init__(
        self,
        routine_repository: RoutineRepository,
        execution_repository: ExecutionRepository,
        validator: Optional[LearningValidator] = None,
        analyzer: Optional[PatternAnalyzer] = None,
        calculator: Optional[ConfidenceCalculator] = None,
    ) -> None:
        """Initializes RoutineLearningEngine with dependencies.

        Args:
            routine_repository: Database repository for routines.
            execution_repository: Database repository for execution history logs.
            validator: Custom validation rules.
            analyzer: Sequence pattern analyzer logic.
            calculator: Confidence computation logic.
        """
        self._routine_repository = routine_repository
        self._execution_repository = execution_repository
        self._validator = validator or LearningValidator()
        self._analyzer = analyzer or PatternAnalyzer()
        self._calculator = calculator or ConfidenceCalculator()

        # Thread-safe cache of rejected triggers to prevent suggesting them again
        self._rejected_lock = threading.Lock()
        self._rejected_triggers: Set[str] = set()

    def record_execution(
        self,
        user_id: int,
        action: str,
        input_parameters: Dict[str, Any],
        status: str,
        duration_ms: Optional[int] = None,
        logs: Optional[str] = None,
    ) -> ExecutionHistoryDomain:
        """Saves a execution outcome event to the database execution history log.

        Args:
            user_id: Owner user identifier.
            action: Capability action executed.
            input_parameters: Params dictionary details.
            status: Outcome status string.
            duration_ms: Execution runtime in milliseconds.
            logs: Diagnostics trace.

        Returns:
            The created ExecutionHistoryDomain object.
        """
        domain = ExecutionHistoryDomain(
            user_id=user_id,
            action=action,
            input_parameters=input_parameters,
            status=status,
            duration_ms=duration_ms,
            logs=logs,
        )
        logger.info(f"Recording execution history entry: {action} ({status})")
        return self._execution_repository.create(domain)

    def analyze_execution_history(self, user_id: int, min_confidence: float = 0.3) -> List[RoutineSuggestion]:
        """Analyzes logs, mines recurring sequences, and produces routine suggestions.

        Args:
            user_id: Owner user identifier.
            min_confidence: Confidence threshold floor (e.g. 0.3).

        Returns:
            List of generated RoutineSuggestion objects.
        """
        executions = self._execution_repository.search({"user_id": user_id})
        if not executions:
            return []

        # Find repeating sequences
        patterns = self._analyzer.analyze(executions)
        suggestions: List[RoutineSuggestion] = []

        # Fetch existing active routines
        active_routines = self._routine_repository.search({"user_id": user_id, "is_active": True})
        active_triggers = {r.trigger_event for r in active_routines}

        with self._rejected_lock:
            ignored_triggers = set(self._rejected_triggers)

        for p in patterns:
            trigger = p["trigger_event"]

            # Skip if already learned or explicitly rejected
            if trigger in active_triggers or trigger in ignored_triggers:
                continue

            confidence = self._calculator.calculate(
                occurrences=p["occurrences"],
                total_sessions=p["total_sessions"],
                success_rate=p["success_rate"],
            )

            if confidence >= min_confidence:
                suggestions.append(
                    RoutineSuggestion(
                        trigger_event=trigger,
                        action_sequence=p["action_sequence"],
                        confidence_score=confidence,
                    )
                )

        return suggestions

    def accept_suggestion(self, user_id: int, suggestion: RoutineSuggestion) -> RoutineLearningDomain:
        """Validates and persists a suggested routine into the learned database.

        Args:
            user_id: Owner user identifier.
            suggestion: RoutineSuggestion to accept.

        Returns:
            The persisted RoutineLearningDomain object.
        """
        self._validator.validate_routine(
            suggestion.trigger_event,
            suggestion.action_sequence,
            suggestion.confidence_score,
        )

        logger.info(
            "Accepting routine suggestion",
            extra={"user_id": user_id, "trigger_event": suggestion.trigger_event},
        )

        domain = RoutineLearningDomain(
            user_id=user_id,
            trigger_event=suggestion.trigger_event,
            action_sequence=suggestion.action_sequence,
            confidence_score=suggestion.confidence_score,
            is_active=True,
        )
        return self._routine_repository.create(domain)

    def reject_suggestion(self, user_id: int, trigger_event: str) -> None:
        """Mutes a suggested trigger event to prevent recommending it in subsequent runs.

        Args:
            user_id: Owner user identifier.
            trigger_event: Trigger identifier description.
        """
        logger.info(
            "Rejecting routine suggestion trigger",
            extra={"user_id": user_id, "trigger_event": trigger_event},
        )
        with self._rejected_lock:
            self._rejected_triggers.add(trigger_event)

    def delete_routine(self, user_id: int, routine_id: int) -> bool:
        """Deletes a learned routine by ID.

        Args:
            user_id: Owner user identifier.
            routine_id: Routine primary identifier.

        Returns:
            True if deleted, False if not found.
        """
        routine = self._routine_repository.get_by_id(routine_id)
        if routine is None or routine.user_id != user_id:
            return False

        logger.info(
            "Deleting learned routine",
            extra={"user_id": user_id, "routine_id": routine_id},
        )
        return self._routine_repository.delete(routine_id)

    def list_routines(self, user_id: int) -> List[RoutineLearningDomain]:
        """Lists active learned routines for a user.

        Args:
            user_id: Owner user identifier.

        Returns:
            List of RoutineLearningDomain objects.
        """
        return self._routine_repository.search({"user_id": user_id, "is_active": True})
