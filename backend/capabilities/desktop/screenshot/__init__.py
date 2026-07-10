"""Screenshot and screen utilities submodule for Auralis."""

from __future__ import annotations

from .models import ScreenshotDetails
from .capture_manager import CaptureManager
from .annotation import Annotation
from .screen_recorder import ScreenRecorder
from .screenshot_service import ScreenshotService

__all__ = [
    "ScreenshotDetails",
    "CaptureManager",
    "Annotation",
    "ScreenRecorder",
    "ScreenshotService",
]
