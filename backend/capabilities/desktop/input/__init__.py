"""Input automation capability submodule for Auralis."""

from __future__ import annotations

from .models import InputCoordinate
from .keyboard_controller import KeyboardController
from .mouse_controller import MouseController
from .shortcut_manager import ShortcutManager
from .macro_executor import MacroExecutor
from .input_service import InputService

__all__ = [
    "InputCoordinate",
    "KeyboardController",
    "MouseController",
    "ShortcutManager",
    "MacroExecutor",
    "InputService",
]
