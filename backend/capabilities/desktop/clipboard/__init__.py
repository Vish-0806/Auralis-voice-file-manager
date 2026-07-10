"""Clipboard automation capability submodule for Auralis."""

from __future__ import annotations

from .models import ClipboardEntry
from .clipboard_manager import ClipboardManager
from .clipboard_history import ClipboardHistory
from .clipboard_service import ClipboardService

__all__ = [
    "ClipboardEntry",
    "ClipboardManager",
    "ClipboardHistory",
    "ClipboardService",
]
