"""Manages text notifications and pub-sub for assistant voice states."""

import threading
import time
from typing import Callable, Dict, List, Optional
from utils.logger import get_logger

from voice.ux.models import AssistantStatus, UXNotification

logger = get_logger(__name__)

# Standard notification messages mapped to states
DEFAULT_NOTIFICATIONS: Dict[AssistantStatus, str] = {
    AssistantStatus.SLEEPING: "Sleeping...",
    AssistantStatus.WAKE_DETECTED: "Wake word detected.",
    AssistantStatus.LISTENING: "Listening...",
    AssistantStatus.PROCESSING: "Processing...",
    AssistantStatus.SPEAKING: "Responding...",
    AssistantStatus.WAITING: "Done.",
    AssistantStatus.ERROR: "Error",
}


class NotificationManager:
    """Publishes text feedback messages and maintains listener subscriber lists."""

    def __init__(self, custom_messages: Optional[Dict[AssistantStatus, str]] = None) -> None:
        """Initializes the NotificationManager.

        Args:
            custom_messages: Optional message mapping overrides.
        """
        self._message_map = dict(DEFAULT_NOTIFICATIONS)
        if custom_messages is not None:
            self._message_map.update(custom_messages)

        self._listeners: List[Callable[[UXNotification], None]] = []
        self._lock = threading.Lock()

    def get_message_for_status(self, status: AssistantStatus) -> str:
        """Retrieves the default text message configured for the status state.

        Args:
            status: The AssistantStatus state.

        Returns:
            The plain text message string.
        """
        return self._message_map.get(status, "")

    def publish(self, status: AssistantStatus, custom_message: Optional[str] = None) -> UXNotification:
        """Publishes a UXNotification and broadcasts it to all listeners.

        Args:
            status: The related AssistantStatus state.
            custom_message: Custom message string override. If None, uses default.

        Returns:
            The created and published UXNotification.
        """
        message = custom_message if custom_message is not None else self.get_message_for_status(status)
        notification = UXNotification(
            status=status,
            message=message,
            timestamp=time.time(),
        )

        logger.info("UX Notification: [%s] %s", status.name, message)

        listeners_to_notify = []
        with self._lock:
            listeners_to_notify = list(self._listeners)

        for listener in listeners_to_notify:
            try:
                listener(notification)
            except Exception as e:
                logger.error("Error in notification listener callback: %s", e)

        return notification

    def register_listener(self, callback: Callable[[UXNotification], None]) -> None:
        """Registers a callback to receive published UXNotifications.

        Args:
            callback: Listener function with signature: (notification: UXNotification) -> None.
        """
        with self._lock:
            if callback not in self._listeners:
                logger.debug("Registering notification listener: %s", callback)
                self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[UXNotification], None]) -> None:
        """Unregisters a previously added notification listener.

        Args:
            callback: The listener function to remove.
        """
        with self._lock:
            if callback in self._listeners:
                logger.debug("Unregistering notification listener: %s", callback)
                self._listeners.remove(callback)

    def clear_listeners(self) -> None:
        """Removes all registered notification listeners."""
        with self._lock:
            self._listeners.clear()
