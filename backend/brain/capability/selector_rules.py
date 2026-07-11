"""Rule-based routing definitions for capability selection in Auralis."""

from __future__ import annotations

import logging
from core.intents import Intent


class SelectorRules:
    """Evaluates routing rules to map intents and metadata to system capabilities."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes SelectorRules.

        Args:
            logger: Optional custom logger for routing rule diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def route_intent(self, intent: Intent, target: str | None = None) -> str:
        """Applies rule-based routing to determine capability name from an intent.

        Args:
            intent: The system Intent of the action.
            target: The optional target argument.

        Returns:
            The name of the resolved capability (e.g., 'File', 'Desktop', etc.).
        """
        intent_value = intent.value.upper()

        if intent in {
            Intent.CREATE_FOLDER,
            Intent.DELETE_FOLDER,
            Intent.ORGANIZE_FOLDER,
            Intent.COPY_FILE_PATH,
        } or "FOLDER" in intent_value or "FILE" in intent_value:
            return "File"

        if intent in {
            Intent.RUN_WORKFLOW,
            Intent.LIST_WORKFLOWS,
        } or "WORKFLOW" in intent_value:
            return "Workflow"

        if intent in {
            Intent.OPEN_APPLICATION,
            Intent.CLOSE_APPLICATION,
            Intent.RESTART_APPLICATION,
            Intent.LIST_RUNNING_APPLICATIONS,
            Intent.MINIMIZE_WINDOW,
            Intent.MAXIMIZE_WINDOW,
            Intent.RESTORE_WINDOW,
            Intent.FOCUS_WINDOW,
            Intent.CLOSE_WINDOW,
            Intent.SHOW_DESKTOP,
            Intent.LIST_WINDOWS,
            Intent.SET_VOLUME,
            Intent.MUTE,
            Intent.UNMUTE,
            Intent.SET_BRIGHTNESS,
            Intent.LOCK_PC,
            Intent.SLEEP_PC,
            Intent.SHUTDOWN_PC,
            Intent.RESTART_PC,
            Intent.HIBERNATE_PC,
            Intent.ENABLE_WIFI,
            Intent.DISABLE_WIFI,
            Intent.ENABLE_BLUETOOTH,
            Intent.DISABLE_BLUETOOTH,
            Intent.COPY_SELECTION,
            Intent.PASTE,
            Intent.CLEAR_CLIPBOARD,
            Intent.SHOW_CLIPBOARD,
            Intent.SAVE_CLIPBOARD,
            Intent.TAKE_SCREENSHOT,
            Intent.CAPTURE_WINDOW,
            Intent.CAPTURE_MONITOR,
            Intent.DELAYED_SCREENSHOT,
            Intent.COPY_SCREENSHOT,
            Intent.SAVE_SCREENSHOT,
            Intent.START_RECORDING,
            Intent.STOP_RECORDING,
            Intent.TYPE_TEXT,
            Intent.PRESS_KEY,
            Intent.PRESS_SHORTCUT,
            Intent.MOVE_MOUSE,
            Intent.CLICK_MOUSE,
            Intent.DOUBLE_CLICK,
            Intent.RIGHT_CLICK,
            Intent.SCROLL,
            Intent.DRAG_DROP,
            Intent.RUN_MACRO,
        } or "MOUSE" in intent_value or "KEY" in intent_value or "WINDOW" in intent_value or "SCREENSHOT" in intent_value:
            return "Desktop"

        if "SPEAK" in intent_value or "VOICE" in intent_value:
            return "Voice"

        target_upper = target.upper() if target else ""
        if "BROWSER" in intent_value or "URL" in intent_value or "WEB" in intent_value or "BROWSER" in target_upper or "URL" in target_upper or "WEB" in target_upper:
            return "Browser"
        if "DEVELOP" in intent_value or "CODE" in intent_value or "COMPILE" in intent_value or "DEVELOP" in target_upper or "CODE" in target_upper or "COMPILE" in target_upper:
            return "Developer"
        if "MEM" in intent_value or "RECALL" in intent_value or "REMEMBER" in intent_value or "MEM" in target_upper or "RECALL" in target_upper or "REMEMBER" in target_upper:
            return "Memory"

        self._logger.warning("No custom selector rule matched intent; falling back", extra={"intent": intent.value})
        return "Unknown"
