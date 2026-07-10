"""Low-level OS clipboard interaction using win32clipboard."""

from __future__ import annotations

import logging
import os
import win32clipboard


class ClipboardManager:
    """Manages raw read, write, and format detection operations on the OS clipboard."""

    CF_HDROP = 15

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ClipboardManager.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def read_clipboard(self) -> str:
        """Reads unicode text from the system clipboard.

        Returns:
            The text content, or empty string if not text or empty.
        """

        if os.name != "nt":
            self._logger.warning("Clipboard read is only supported on Windows")
            return ""

        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                return str(data)
            return ""
        except Exception as exc:
            self._logger.error("Failed to read system clipboard", exc_info=exc)
            return ""
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def write_clipboard(self, content: str) -> None:
        """Writes unicode text to the system clipboard.

        Args:
            content: The text content to write.
        """

        if os.name != "nt":
            self._logger.warning("Clipboard write is only supported on Windows")
            return

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(content, win32clipboard.CF_UNICODETEXT)
        except Exception as exc:
            self._logger.error("Failed to write system clipboard", exc_info=exc)
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def clear_clipboard(self) -> None:
        """Clears all clipboard contents."""

        if os.name != "nt":
            return

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
        except Exception as exc:
            self._logger.error("Failed to clear system clipboard", exc_info=exc)
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def detect_clipboard_type(self) -> str:
        """Detects the current content format stored in the clipboard.

        Returns:
            One of 'text', 'file_paths', 'image', or 'empty'.
        """

        if os.name != "nt":
            return "empty"

        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return "text"
            if win32clipboard.IsClipboardFormatAvailable(self.CF_HDROP):
                return "file_paths"
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP):
                return "image"
            return "empty"
        except Exception as exc:
            self._logger.error("Failed to detect clipboard content format", exc_info=exc)
            return "empty"
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def get_file_paths(self) -> list[str]:
        """Retrieves file path listings from clipboard drop files (CF_HDROP).

        Returns:
            List of absolute file paths if available, otherwise empty.
        """

        if os.name != "nt":
            return []

        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(self.CF_HDROP):
                paths = win32clipboard.GetClipboardData(self.CF_HDROP)
                if isinstance(paths, tuple):
                    return list(paths)
                return []
            return []
        except Exception as exc:
            self._logger.error("Failed to query clipboard file drop paths", exc_info=exc)
            return []
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
