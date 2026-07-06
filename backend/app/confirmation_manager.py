"""
Auralis Application Confirmation State Manager
Manages application state, specifically pending actions for confirmation workflows
and support for future multi-step workflows.
"""

import time
from typing import Any, Dict, List, Optional


class ConfirmationManager:
    """Manages application state, specifically pending actions for confirmation workflows

    and future multi-step automation workflows.
    """

    _pending_action: Optional[str] = None
    _pending_target: Optional[str] = None
    _pending_destination: Optional[str] = None
    _timestamp: Optional[float] = None
    _workflow_steps: List[Dict[str, Any]] = []

    @classmethod
    def set_pending_action(
        cls, action: str, target: str, destination: Optional[str] = None
    ) -> None:
        """Sets the current pending action with target, optional destination, and timestamp."""
        cls._pending_action = action
        cls._pending_target = target
        cls._pending_destination = destination
        cls._timestamp = time.time()

    @classmethod
    def get_pending_action(cls) -> Optional[Dict[str, Any]]:
        """Retrieves the current pending action details as a dictionary.

        Returns None if no action is pending.
        """
        if cls._pending_action is None:
            return None
        return {
            "pending_action": cls._pending_action,
            "pending_target": cls._pending_target,
            "pending_destination": cls._pending_destination,
            "timestamp": cls._timestamp,
        }

    @classmethod
    def clear_pending_action(cls) -> None:
        """Clears all pending action state and resets workflow steps."""
        cls._pending_action = None
        cls._pending_target = None
        cls._pending_destination = None
        cls._timestamp = None
        cls._workflow_steps = []

    @classmethod
    def add_workflow_step(cls, step_data: Dict[str, Any]) -> None:
        """Adds a workflow step for tracking multi-step workflows."""
        cls._workflow_steps.append(step_data)

    @classmethod
    def get_workflow_steps(cls) -> List[Dict[str, Any]]:
        """Retrieves the list of all recorded workflow steps."""
        return cls._workflow_steps
