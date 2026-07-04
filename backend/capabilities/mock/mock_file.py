"""Temporary mock file capability used for dispatcher phase validation."""

from __future__ import annotations

from typing import Any

from core.interfaces import ICapability


class MockFileCapability(ICapability):
    """Returns deterministic responses for supported file intents."""

    def __init__(self) -> None:
        self._name = "mock_file"

    @property
    def name(self) -> str:
        """Returns the stable capability name."""

        return self._name

    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Builds a mock response for the requested action.

        Args:
            action: The intent/action to execute.
            arguments: Structured arguments supplied by the dispatcher.

        Returns:
            A dictionary containing the mock response payload.
        """

        target = self._resolve_target(arguments)
        response = self._build_response(action, target)
        return {
            "response": response,
            "action": action,
            "target": target,
            "arguments": arguments,
        }

    def _resolve_target(self, arguments: dict[str, Any]) -> str:
        """Extracts the target value from the arguments."""

        target = arguments.get("target")
        if isinstance(target, str) and target.strip():
            return target.strip()

        return "unknown target"

    def _build_response(self, action: str, target: str) -> str:
        """Builds the user-facing response for a supported action."""

        if action == "OPEN_FOLDER":
            return f"Opening {target}..."

        if action == "OPEN_FILE":
            return f"Opening file {target}..."

        if action == "SEARCH_FILE":
            return f"Searching for {target}..."

        if action == "LIST_DIRECTORY":
            return f"Listing contents of {target}..."

        return f"Unsupported action {action} for {target}."


__all__ = ["MockFileCapability"]