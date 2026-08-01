"""Notification Service implementation (Phase 11.5).

Provides validation, dispatch, and history logging of desktop notifications
with support for priority levels (INFO, WARNING, ERROR, SUCCESS) and graceful fallbacks.
"""

from datetime import datetime, timezone
import threading
import uuid
from typing import List, Optional

from brain.os.desktop.desktop_models import DesktopNotification, NotificationLevel
from brain.os.desktop.exceptions import NotificationError
from brain.os.desktop.interfaces import INotificationService


class NotificationService(INotificationService):
    """Thread-safe desktop notification service."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._history: List[DesktopNotification] = []

    def send_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        duration_seconds: float = 5.0,
    ) -> DesktopNotification:
        """Dispatch a desktop notification."""
        if not title and not message:
            raise NotificationError("Notification title and message cannot both be empty")

        with self._lock:
            notif_id = f"notif_{uuid.uuid4().hex[:8]}"
            notif = DesktopNotification(
                notification_id=notif_id,
                title=title or "Auralis Notification",
                message=message or "",
                level=level,
                duration_seconds=duration_seconds,
                timestamp=datetime.now(timezone.utc),
            )

            # Log to internal history
            self._history.append(notif)
            return notif

    def get_history(self) -> List[DesktopNotification]:
        """Get list of dispatched notification history."""
        with self._lock:
            return list(self._history)

    def clear_history(self) -> None:
        """Clear notification history log."""
        with self._lock:
            self._history.clear()
