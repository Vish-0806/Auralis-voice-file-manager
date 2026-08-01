"""Clipboard Service implementation (Phase 11.5).

Provides safe system clipboard reading, writing (text & files), format detection,
and clearing with robust fallback handling for headless or restricted environments.
"""

from datetime import datetime, timezone
import threading
from typing import List, Optional

from brain.os.desktop.desktop_models import ClipboardContent, ClipboardFormat
from brain.os.desktop.exceptions import ClipboardError
from brain.os.desktop.interfaces import IClipboardService


class ClipboardService(IClipboardService):
    """Thread-safe system clipboard service with fallback buffer support."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._buffer_text: Optional[str] = None
        self._buffer_files: List[str] = []
        self._buffer_format: ClipboardFormat = ClipboardFormat.UNKNOWN

    def _read_sys_clipboard(self) -> Optional[str]:
        """Try reading text from system clipboard using tkinter or fallback."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            txt = root.clipboard_get()
            root.destroy()
            return txt
        except Exception:
            return None

    def _write_sys_clipboard(self, text: str) -> bool:
        """Try writing text to system clipboard using tkinter or fallback."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True
        except Exception:
            return False

    def read_content(self) -> ClipboardContent:
        """Read current data content from system clipboard."""
        with self._lock:
            sys_text = self._read_sys_clipboard()
            if sys_text is not None:
                return ClipboardContent(
                    format=ClipboardFormat.TEXT,
                    text_content=sys_text,
                    file_paths=[],
                    byte_size=len(sys_text.encode("utf-8")),
                    timestamp=datetime.now(timezone.utc),
                )

            # Fallback to buffer
            if self._buffer_files:
                return ClipboardContent(
                    format=ClipboardFormat.FILES,
                    text_content=None,
                    file_paths=list(self._buffer_files),
                    byte_size=sum(len(f.encode("utf-8")) for f in self._buffer_files),
                    timestamp=datetime.now(timezone.utc),
                )
            elif self._buffer_text is not None:
                return ClipboardContent(
                    format=ClipboardFormat.TEXT,
                    text_content=self._buffer_text,
                    file_paths=[],
                    byte_size=len(self._buffer_text.encode("utf-8")),
                    timestamp=datetime.now(timezone.utc),
                )
            else:
                return ClipboardContent(
                    format=ClipboardFormat.UNKNOWN,
                    text_content=None,
                    file_paths=[],
                    byte_size=0,
                    timestamp=datetime.now(timezone.utc),
                )

    def write_text(self, text: str) -> bool:
        """Write string text to system clipboard."""
        with self._lock:
            if text is None:
                text = ""

            self._buffer_text = text
            self._buffer_files = []
            self._buffer_format = ClipboardFormat.TEXT

            self._write_sys_clipboard(text)
            return True

    def write_files(self, files: List[str]) -> bool:
        """Write file paths to system clipboard."""
        with self._lock:
            self._buffer_files = list(files or [])
            self._buffer_text = "\n".join(self._buffer_files)
            self._buffer_format = ClipboardFormat.FILES

            self._write_sys_clipboard(self._buffer_text)
            return True

    def clear(self) -> bool:
        """Clear all contents from system clipboard."""
        with self._lock:
            self._buffer_text = None
            self._buffer_files = []
            self._buffer_format = ClipboardFormat.UNKNOWN
            self._write_sys_clipboard("")
            return True
