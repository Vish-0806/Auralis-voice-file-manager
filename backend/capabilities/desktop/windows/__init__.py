"""Window management submodule for Auralis."""

from __future__ import annotations

from .models import WindowDetails
from .window_manager import WindowManager
from .window_resolver import WindowResolver
from .window_service import WindowService

__all__ = [
    "WindowDetails",
    "WindowManager",
    "WindowResolver",
    "WindowService",
]
