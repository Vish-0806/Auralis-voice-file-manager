"""Automation Trigger Engine for the Auralis Automation & Scheduling Runtime (Phase 12.6).

Evaluates trigger criteria for Time, Manual, System Event, Task Completion, and Custom trigger types.
Provider-independent with zero platform-specific code.
"""

from typing import Any, Dict, Optional

from brain.execution.automation.interfaces import IAutomationTriggerEngine
from brain.execution.automation.automation_models import (
    AutomationTrigger,
    AutomationTriggerType,
)


class AutomationTriggerEngine(IAutomationTriggerEngine):
    """Trigger engine evaluating trigger patterns and event criteria against context parameters."""

    def evaluate_trigger(
        self,
        trigger: AutomationTrigger,
        event_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluate whether a trigger matches given event context criteria.

        Args:
            trigger: AutomationTrigger object.
            event_context: Optional event dictionary.

        Returns:
            True if trigger criteria match, False otherwise.
        """
        context = event_context or {}

        if trigger.trigger_type == AutomationTriggerType.MANUAL:
            # Manual triggers fire when explicitly invoked or matching "manual" event
            return context.get("event_type") == "MANUAL" or context.get("manual_override", False)

        elif trigger.trigger_type == AutomationTriggerType.TIME:
            # Time triggers evaluated via scheduler schedule calculation
            return True

        elif trigger.trigger_type == AutomationTriggerType.SYSTEM_EVENT:
            if not trigger.event_pattern:
                return True
            pattern = trigger.event_pattern.lower()
            event_name = str(context.get("event_name", "")).lower()
            return pattern in event_name or event_name == pattern

        elif trigger.trigger_type == AutomationTriggerType.TASK_COMPLETION:
            if context.get("event_type") != "TASK_COMPLETION":
                return False
            if trigger.condition:
                target_task = trigger.condition
                completed_task = context.get("task_id", "")
                return target_task == completed_task or target_task == "*"
            return True

        elif trigger.trigger_type == AutomationTriggerType.FILE_SYSTEM:
            if context.get("event_type") != "FILE_SYSTEM":
                return False
            if trigger.event_pattern:
                target_file = str(context.get("file_path", "")).lower()
                return trigger.event_pattern.lower() in target_file
            return True

        elif trigger.trigger_type == AutomationTriggerType.CUSTOM:
            if trigger.condition:
                return bool(context.get(trigger.condition, False))
            return True

        return False
