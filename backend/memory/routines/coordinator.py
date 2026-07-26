"""Routine Learning Coordinator orchestrating the routines subsystem."""

import logging
from typing import Any, List, Optional
from memory.routines.models import RoutineCandidate, RoutineDefinitionDomain
from memory.routines.pattern_detector import RoutinePatternDetector
from memory.routines.validator import RoutineValidator
from memory.routines.optimizer import RoutineOptimizer
from memory.routines.library import RoutineLibrary
from memory.routines.matcher import RoutineMatcher
from memory.routines.scheduler import RoutineScheduler
from memory.routines.monitor import RoutineRuntimeMonitor

logger = logging.getLogger(__name__)


class RoutineLearningCoordinator:
    """Orchestrates pattern mining, candidate validation, optimizations, scheduling, and catalog matching."""

    def __init__(
        self,
        pattern_detector: RoutinePatternDetector,
        validator: RoutineValidator,
        optimizer: RoutineOptimizer,
        library: RoutineLibrary,
        matcher: RoutineMatcher,
        scheduler: RoutineScheduler,
        monitor: RoutineRuntimeMonitor,
    ) -> None:
        """Initializes the coordinator with all routines subsystem components."""
        self.pattern_detector = pattern_detector
        self.validator = validator
        self.optimizer = optimizer
        self.library = library
        self.matcher = matcher
        self.scheduler = scheduler
        self.monitor = monitor

    def process_execution_history(self, user_id: int, executions: List[Any]) -> List[RoutineCandidate]:
        """Analyzes recent execution history to discover validated routine candidates."""
        candidates = self.pattern_detector.detect_candidates(executions)
        valid_candidates = []
        for c in candidates:
            if self.validator.validate_routine(c):
                valid_candidates.append(c)

        logger.info(
            f"Processed history for user {user_id}. Found {len(candidates)} candidates, {len(valid_candidates)} validated."
        )
        return valid_candidates

    def promote_candidate(
        self, user_id: int, candidate: RoutineCandidate, name: str
    ) -> Optional[RoutineDefinitionDomain]:
        """Validates, optimizes, and registers a candidate routine into the library catalog."""
        if not self.validator.validate_routine(candidate):
            logger.warning("Promotion aborted: Candidate failed semantic routine validation checks.")
            return None

        # Run optimization step
        steps = candidate.action_sequence.get("steps", [])
        optimised_steps, report = self.optimizer.optimize_sequence(steps)

        # Assemble definition model
        domain = RoutineDefinitionDomain(
            user_id=user_id,
            name=name,
            description=f"Auto-promoted routine from trigger event: '{candidate.trigger_event}'",
            steps=optimised_steps,
            trigger_condition={"trigger_event": candidate.trigger_event},
            metadata_info={
                "original_report": report.model_dump(),
                "category": "automation",
                "tags": [candidate.trigger_event],
            },
        )

        return self.library.register_routine(domain)
