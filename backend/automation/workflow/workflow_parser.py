"""Workflow name parser and normalized lookup mapper."""

from __future__ import annotations

import logging


class WorkflowParser:
    """Parses user workflow request messages into normalized workflow names."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the WorkflowParser.

        Args:
            logger: Optional logger.
        """

        self._logger = logger or logging.getLogger(__name__)

    def parse_workflow_name(self, text: str) -> str:
        """Normalizes and translates user input phrases to workflow names.

        Args:
            text: User command string.

        Returns:
            The normalized workflow key.
        """

        val = text.strip().lower()
        if "start coding" in val or "coding" in val:
            return "Start Coding"
        if "study mode" in val or "study" in val:
            return "Study Mode"
        if "meeting mode" in val or "meeting" in val:
            return "Meeting Mode"
        if "movie mode" in val or "movie" in val:
            return "Movie Mode"
        if "clean workspace" in val or "clean" in val or "cleanup" in val:
            return "Clean Workspace"
        
        return text.title()
