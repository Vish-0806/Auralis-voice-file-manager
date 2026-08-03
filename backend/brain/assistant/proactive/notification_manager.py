"""Notification Manager implementation for Auralis (Phase 13.8).

Manages assistant-level notification creation, priority ordering, dismissal, archiving, and expiration.
Does NOT invoke OS or desktop notifications. Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional

from brain.assistant.proactive.exceptions import NotificationException
from brain.assistant.proactive.interfaces import INotificationManager
from brain.assistant.proactive.models import (
    NotificationType,
    ProactiveNotification,
    SuggestionPriority,
)

logger = logging.getLogger(__name__)

_PRIORITY_RANK = {
    SuggestionPriority.MANDATORY: 5,
    SuggestionPriority.CRITICAL: 4,
    SuggestionPriority.HIGH: 3,
    SuggestionPriority.MEDIUM: 2,
    SuggestionPriority.LOW: 1,
}


class NotificationManager(INotificationManager):
    """Thread-safe manager for assistant-level ProactiveNotification objects."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._notifications: Dict[str, ProactiveNotification] = {}

        # Statistics
        self._total_created = 0
        self._dismissed_count = 0
        self._archived_count = 0

    @property
    def total_created_count(self) -> int:
        with self._lock:
            return self._total_created

    @property
    def dismissed_count(self) -> int:
        with self._lock:
            return self._dismissed_count

    @property
    def archived_count(self) -> int:
        with self._lock:
            return self._archived_count

    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "INFO",
        priority: str = "MEDIUM",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProactiveNotification:
        """Create and register a new assistant-level ProactiveNotification."""
        if not title or not message:
            raise NotificationException("title and message cannot be empty")

        with self._lock:
            try:
                ntype = NotificationType(notification_type)
            except ValueError:
                ntype = NotificationType.INFO

            try:
                prio = SuggestionPriority(priority)
            except ValueError:
                prio = SuggestionPriority.MEDIUM

            notification = ProactiveNotification(
                title=title,
                message=message,
                notification_type=ntype,
                priority=prio,
                read=False,
                dismissed=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            self._notifications[notification.notification_id] = notification
            self._total_created += 1

            logger.info("Created ProactiveNotification id=%s title='%s'", notification.notification_id, title)
            return notification

    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss an active notification thread-safely."""
        with self._lock:
            notif = self._notifications.get(notification_id)
            if not notif or notif.dismissed:
                return False

            updated = ProactiveNotification(
                notification_id=notif.notification_id,
                title=notif.title,
                message=notif.message,
                notification_type=notif.notification_type,
                priority=notif.priority,
                read=True,
                dismissed=True,
                archived=notif.archived,
                expires_at=notif.expires_at,
                created_at=notif.created_at,
                metadata=notif.metadata,
            )
            self._notifications[notification_id] = updated
            self._dismissed_count += 1
            logger.info("Dismissed ProactiveNotification id=%s", notification_id)
            return True

    def archive_notification(self, notification_id: str) -> bool:
        """Archive a notification thread-safely."""
        with self._lock:
            notif = self._notifications.get(notification_id)
            if not notif or notif.archived:
                return False

            updated = ProactiveNotification(
                notification_id=notif.notification_id,
                title=notif.title,
                message=notif.message,
                notification_type=notif.notification_type,
                priority=notif.priority,
                read=True,
                dismissed=notif.dismissed,
                archived=True,
                expires_at=notif.expires_at,
                created_at=notif.created_at,
                metadata=notif.metadata,
            )
            self._notifications[notification_id] = updated
            self._archived_count += 1
            logger.info("Archived ProactiveNotification id=%s", notification_id)
            return True

    def list_active_notifications(self) -> List[ProactiveNotification]:
        """List active non-dismissed and non-expired notifications ordered by priority."""
        with self._lock:
            now = datetime.now(timezone.utc)
            active: List[ProactiveNotification] = []

            for notif in self._notifications.values():
                if notif.dismissed or notif.archived:
                    continue
                if notif.expires_at and notif.expires_at < now:
                    continue
                active.append(notif)

            # Sort by priority rank descending
            active.sort(key=lambda n: _PRIORITY_RANK.get(n.priority, 2), reverse=True)
            return active

    def clear(self) -> None:
        """Reset notification manager state."""
        with self._lock:
            self._notifications.clear()
            self._total_created = 0
            self._dismissed_count = 0
            self._archived_count = 0
