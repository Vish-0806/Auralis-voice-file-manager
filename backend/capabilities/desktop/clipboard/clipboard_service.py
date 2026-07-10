"""Clipboard Service coordinating raw manager inputs and history tracking."""

from __future__ import annotations

import logging
import os
from datetime import datetime, UTC
from .models import ClipboardEntry
from .clipboard_manager import ClipboardManager
from .clipboard_history import ClipboardHistory


class ClipboardService:
    """Orchestrates system clipboard reads, writes, history, and exports."""

    def __init__(
        self,
        manager: ClipboardManager | None = None,
        history: ClipboardHistory | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ClipboardService.

        Args:
            manager: Custom clipboard manager.
            history: Custom clipboard history.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._manager = manager or ClipboardManager(logger=self._logger)
        self._history = history or ClipboardHistory()

    def copy(self, text: str) -> None:
        """Copies text content to the clipboard and appends to history."""

        self._logger.info("Copying text to clipboard")
        self._manager.write_clipboard(text)
        
        entry = ClipboardEntry(
            content=text,
            content_type="text",
            timestamp=datetime.now(UTC),
            size_bytes=len(text.encode("utf-8")),
        )
        self._history.add_entry(entry)

    def paste(self) -> str:
        """Reads unicode text from the clipboard.

        Returns:
            The text content.
        """

        self._logger.info("Pasting text from clipboard")
        return self._manager.read_clipboard()

    def clear(self) -> None:
        """Clears system clipboard and wipes history."""

        self._logger.info("Clearing clipboard and history")
        self._manager.clear_clipboard()
        self._history.clear_history()

    def get_contents(self) -> ClipboardEntry:
        """Retrieves current clipboard contents as structured details.

        Returns:
            A ClipboardEntry details model.
        """

        content_type = self._manager.detect_clipboard_type()
        content = ""
        size = 0

        if content_type == "text":
            content = self._manager.read_clipboard()
            size = len(content.encode("utf-8"))
        elif content_type == "file_paths":
            paths = self._manager.get_file_paths()
            content = ", ".join(paths)
            size = len(content.encode("utf-8"))
        elif content_type == "image":
            content = "[Image Data]"
            size = 0
        else:
            content_type = "empty"
            content = ""

        entry = ClipboardEntry(
            content=content,
            content_type=content_type,
            timestamp=datetime.now(UTC),
            size_bytes=size,
        )
        self._history.add_entry(entry)
        return entry

    def save_to_file(self, file_path: str | None = None) -> bool:
        """Saves current clipboard text content to a destination file.

        Args:
            file_path: Target text file location.

        Returns:
            True if write succeeded.
        """

        content = self.paste()
        if not content:
            self._logger.warning("Clipboard is empty, nothing to export to file.")
            return False

        if not file_path:
            file_path = os.path.join(os.getcwd(), "clipboard_export.txt")

        try:
            parent = os.path.dirname(file_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._logger.info("Saved clipboard to file", extra={"path": file_path})
            return True
        except Exception as exc:
            self._logger.error("Failed to save clipboard to file", exc_info=exc)
            return False

    def copy_file_path(self, file_path: str) -> None:
        """Copies target file path representation to the clipboard."""

        self._logger.info("Copying file path to clipboard", extra={"path": file_path})
        self.copy(file_path)

    def get_history_entries(self) -> list[ClipboardEntry]:
        """Returns the in-memory FIFO deque history."""

        return self._history.get_history()
