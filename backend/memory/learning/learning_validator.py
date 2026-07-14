"""Routine learning data structures validator."""

from typing import Any, Dict, List
from memory.learning.learning_models import InvalidRoutineError


class LearningValidator:
    """Validates structural constraints on trigger events, confidence scores, and action lists."""

    @staticmethod
    def validate_routine(trigger_event: str, action_sequence: Dict[str, Any], confidence_score: float) -> None:
        """Validates trigger and action properties.

        Args:
            trigger_event: Trigger event name.
            action_sequence: Sequence dict of actions (must contain a 'steps' list).
            confidence_score: Score to validate.

        Raises:
            InvalidRoutineError: If any condition fails validation checks.
        """
        if not trigger_event or not isinstance(trigger_event, str) or not trigger_event.strip():
            raise InvalidRoutineError("Routine trigger_event must be a non-empty string.")

        if not isinstance(action_sequence, dict):
            raise InvalidRoutineError("Routine action_sequence must be a dictionary.")

        steps = action_sequence.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise InvalidRoutineError("Routine action_sequence 'steps' must be a non-empty list.")

        for idx, action_item in enumerate(steps):
            if not isinstance(action_item, dict):
                raise InvalidRoutineError(f"Action item at index {idx} must be a dictionary.")
            if "action" not in action_item:
                raise InvalidRoutineError(f"Action item at index {idx} is missing the required 'action' string key.")
            action_name = action_item["action"]
            if not isinstance(action_name, str) or not action_name.strip():
                raise InvalidRoutineError(f"Action name at index {idx} must be a non-empty string.")

        if not isinstance(confidence_score, (int, float)) or not (0.0 <= confidence_score <= 1.0):
            raise InvalidRoutineError("Routine confidence_score must be a float between 0.0 and 1.0.")
