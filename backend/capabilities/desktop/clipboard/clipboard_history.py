"""Temporary in-memory clipboard history collection."""

from __future__ import annotations

from collections import deque
# pyrefly: ignore [missing-import]
from .models import ClipboardEntry


class ClipboardHistory:
    """Manages a bounded temporary history of clipboard actions."""

    def __init__(self, max_size: int = 50) -> None:
        """Initializes the ClipboardHistory with a maximum capacity.

        Args:
            max_size: Maximum history records to retain.
        """

        self._history: deque[ClipboardEntry] = deque(maxlen=max_size)

    def add_entry(self, entry: ClipboardEntry) -> None:
        """Adds a new clipboard entry to the history."""

        self._history.append(entry)

    def get_history(self) -> list[ClipboardEntry]:
        """Returns all history items sorted from newest to oldest."""

        return list(reversed(self._history))

    def clear_history(self) -> None:
        """Clears all history entries."""

        self._history.clear()
