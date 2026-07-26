"""Routine Validator evaluating execution safety and semantic completeness."""

import logging
from typing import Any
from core.intents import Intent

logger = logging.getLogger(__name__)


class RoutineValidator:
    """Validates routine candidates and definition sequences before promotion."""

    def __init__(self) -> None:
        self.valid_intents = {item.value for item in Intent}

    def validate_routine(self, routine: Any) -> bool:
        """Validates that a routine sequence conforms to safety, completeness, and ordering checks."""
        steps = getattr(routine, "steps", [])
        if not steps and hasattr(routine, "action_sequence"):
            steps = routine.action_sequence.get("steps", [])

        # 1. Deterministic ordering check (must be a valid list)
        if not isinstance(steps, list) or not steps:
            logger.warning("Validation failed: Steps is empty or not a list")
            return False

        seen_intents = []
        for step in steps:
            # Step completeness check
            intent = step.get("action") or step.get("intent")
            if not intent:
                logger.warning("Validation failed: Step is missing an action or intent identifier")
                return False

            # 2. Unsupported capabilities check
            if intent not in self.valid_intents:
                logger.warning(f"Validation failed: Intent '{intent}' is not supported by Auralis")
                return False

            # 3. Circular dependency check
            if intent in seen_intents:
                logger.warning(f"Validation failed: Circular dependency detected for intent '{intent}'")
                return False
            seen_intents.append(intent)

        # 4. Conflicting intents check (e.g., conflicting actions)
        conflict_pairs = [
            ("MUTE", "SET_VOLUME"),
            ("DISABLE_WIFI", "ENABLE_WIFI"),
            ("MUTE", "UNMUTE"),
            ("LOCK_SCREEN", "UNLOCK_SCREEN"),
        ]
        seen_set = set(seen_intents)
        for act_a, act_b in conflict_pairs:
            if act_a in seen_set and act_b in seen_set:
                logger.warning(f"Validation failed: Conflicting actions detected ('{act_a}' and '{act_b}')")
                return False

        return True

    def requires_user_approval(self, routine: Any) -> bool:
        """Heuristically flags routines that contain high-impact operations for manual approval."""
        steps = getattr(routine, "steps", [])
        if not steps and hasattr(routine, "action_sequence"):
            steps = routine.action_sequence.get("steps", [])

        high_impact_intents = {
            "DELETE_FILE",
            "DELETE_FOLDER",
            "SHUTDOWN",
            "REBOOT",
            "FORMAT_DRIVE",
        }
        for step in steps:
            intent = step.get("action") or step.get("intent")
            if intent in high_impact_intents:
                return True
        return False
