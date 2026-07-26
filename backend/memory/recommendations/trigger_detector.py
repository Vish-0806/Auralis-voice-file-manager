"""Trigger detector module to identify automation opportunities from runtime context."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TriggerEvent(BaseModel):
    """Represents a runtime context event observed in the environment."""

    event_type: str = Field(..., description="Type of context event (e.g. WorkspaceOpened, ApplicationOpened, TimeOfDay, DayOfWeek, PreviousWorkflowCompleted, UserRequestPattern).")
    value: str = Field(..., description="String value associated with the event (e.g. path, application name, time value).")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the event was observed.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary associated with the event.")


class TriggerCondition(BaseModel):
    """Defines criteria matching conditions for triggering suggestions."""

    trigger_type: str = Field(..., description="Expected event type this condition applies to.")
    expected_value: str = Field(..., description="String pattern/value to match against.")
    match_mode: str = Field(default="exact", description="Comparison mode: 'exact' or 'contains'.")


class TriggerEvaluation(BaseModel):
    """Evaluation result detailing whether a trigger condition is satisfied."""

    triggered: bool = Field(..., description="True if the condition was successfully satisfied.")
    matched_event: Optional[TriggerEvent] = Field(default=None, description="The event that satisfied the condition, if triggered.")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Evaluation timestamp.")


class TriggerDetector:
    """Orchestrator for evaluating context events against defined trigger conditions."""

    def evaluate(self, event: TriggerEvent, condition: TriggerCondition) -> TriggerEvaluation:
        """Determines whether a given event satisfies a trigger condition deterministically."""
        # 1. Event Type Match Check
        if event.event_type != condition.trigger_type:
            return TriggerEvaluation(triggered=False, evaluated_at=datetime.now(timezone.utc))

        triggered = False
        val = event.value.strip()
        expected = condition.expected_value.strip()

        # Enforce case-insensitive comparison
        val_lower = val.lower()
        expected_lower = expected.lower()

        # 2. Value Comparison based on type
        if condition.match_mode == "exact":
            triggered = (val_lower == expected_lower)
        elif condition.match_mode == "contains":
            triggered = (expected_lower in val_lower)
        else:
            # Fallback to exact match
            triggered = (val_lower == expected_lower)

        # 3. Return Evaluation Result
        if triggered:
            return TriggerEvaluation(
                triggered=True,
                matched_event=event,
                evaluated_at=datetime.now(timezone.utc)
            )

        return TriggerEvaluation(triggered=False, evaluated_at=datetime.now(timezone.utc))
