"""Screenshot Service coordinating capture management and PIL/win32 adapters."""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime, UTC
from PIL import Image
from .capture_manager import CaptureManager
from .models import ScreenshotDetails


class ScreenshotService:
    """Coordinates screen grabs, folder target resolution, and win32 clipboard copying."""

    def __init__(
        self,
        capture_manager: CaptureManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ScreenshotService.

        Args:
            capture_manager: Custom capture manager.
            logger: Optional logger for service operations.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._capture_manager = capture_manager or CaptureManager(logger=self._logger)
        self._last_capture: Image.Image | None = None

    def capture_fullscreen(self) -> Image.Image:
        """Captures the unified display canvas."""

        img = self._capture_manager.capture_fullscreen()
        self._last_capture = img
        return img

    def capture_active_window(self) -> Image.Image:
        """Captures the active window area."""

        img = self._capture_manager.capture_active_window()
        self._last_capture = img
        return img

    def capture_monitor(self, monitor_num: int) -> Image.Image:
        """Captures the specified monitor index."""

        img = self._capture_manager.capture_monitor(monitor_num)
        self._last_capture = img
        return img

    def capture_delayed(self, delay: float) -> Image.Image:
        """Captures the fullscreen canvas after a delay."""

        img = self._capture_manager.capture_delayed(delay)
        self._last_capture = img
        return img

    def save_image(self, image: Image.Image | None, destination: str | None = None) -> ScreenshotDetails:
        """Saves the screenshot image to a timestamped file path.

        Args:
            image: PIL Image object. If None, captures the current fullscreen.
            destination: Path, directory name, or shortcut ('desktop', 'pictures').

        Returns:
            Structured ScreenshotDetails.
        """

        img = image or self._last_capture or self.capture_fullscreen()
        
        target_dir = os.getcwd()
        if destination:
            resolved_dest = self._resolve_special_folder(destination)
            if os.path.isdir(resolved_dest) or not os.path.splitext(resolved_dest)[1]:
                target_dir = resolved_dest
                save_path = self._get_unique_path(target_dir)
            else:
                save_path = resolved_dest
                if os.path.exists(save_path):
                    directory = os.path.dirname(save_path) or os.getcwd()
                    base_name = os.path.basename(save_path)
                    name, ext = os.path.splitext(base_name)
                    counter = 1
                    while os.path.exists(save_path):
                        save_path = os.path.join(directory, f"{name}_{counter}{ext}")
                        counter += 1
        else:
            save_path = self._get_unique_path(target_dir)

        parent = os.path.dirname(save_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        img.save(save_path, "PNG")
        self._logger.info("Saved screenshot to file", extra={"path": save_path})

        return ScreenshotDetails(
            path=save_path,
            timestamp=datetime.now(UTC),
            width=img.width,
            height=img.height,
            format="PNG",
        )

    def copy_to_clipboard(self, image: Image.Image | None = None) -> bool:
        """Copies the screenshot to the system clipboard as a DIB."""

        img = image or self._last_capture
        if not img:
            self._logger.warning("No screenshot available to copy to clipboard")
            return False

        if os.name != "nt":
            self._logger.warning("Clipboard image copy is only supported on Windows")
            return False

        try:
            import win32clipboard
            output = io.BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            self._logger.info("Successfully copied screenshot image to system clipboard")
            return True
        except Exception as exc:
            self._logger.error("Failed to copy screenshot to clipboard", exc_info=exc)
            return False
        finally:
            try:
                import win32clipboard
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def _resolve_special_folder(self, folder: str) -> str:
        """Resolves folder shortcuts to actual user directory locations."""

        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        normalized = folder.strip().lower()
        if normalized == "desktop":
            return os.path.join(user_profile, "Desktop")
        if normalized in {"pictures", "images"}:
            return os.path.join(user_profile, "Pictures")
        if normalized == "downloads":
            return os.path.join(user_profile, "Downloads")
        if normalized == "documents":
            return os.path.join(user_profile, "Documents")
        return folder

    def _get_unique_path(self, directory: str) -> str:
        """Generates a unique timestamped screenshot path."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"screenshot_{timestamp}"
        candidate = os.path.join(directory, f"{base}.png")
        
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(directory, f"{base}_{counter}.png")
            counter += 1
        return candidate
