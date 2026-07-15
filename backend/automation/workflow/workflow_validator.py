"""Workflow execution safety validator."""

from __future__ import annotations

import logging
import os
from core.intents import Intent
from .models import WorkflowDefinition


class WorkflowValidator:
    """Validates structural dependencies and target resource paths of a workflow."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the WorkflowValidator.

        Args:
            logger: Optional logger for validation diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._known_apps = {
            "VS Code",
            "Terminal",
            "Microsoft Edge",
            "Notepad",
            "Spotify",
            "Chrome",
            "Edge",
            "Calculator",
            "Teams",
        }

    def validate(self, workflow: WorkflowDefinition) -> bool:
        """Validates that a workflow definition's steps are run-ready.

        Args:
            workflow: Definition schema instance.

        Returns:
            True if all dependency checks pass.
        """

        self._logger.info("Validating workflow dependencies", extra={"workflow_name": workflow.name})
        for step in workflow.steps:
            if step.intent in {Intent.OPEN_APPLICATION, Intent.CLOSE_APPLICATION, Intent.RESTART_APPLICATION}:
                if step.target and step.target not in self._known_apps:
                    self._logger.warning(
                        "Application dependency check failed",
                        extra={"app": step.target},
                    )
                    return False

            if step.intent == Intent.OPEN_FOLDER and step.target:
                if os.path.isabs(step.target) and not os.path.exists(step.target):
                    self._logger.warning(
                        "Folder dependency check failed",
                        extra={"path": step.target},
                    )
                    return False

        return True
