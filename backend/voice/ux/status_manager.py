"""Manages and tracks the current assistant voice state thread-safely."""

import threading
from typing import Callable, List
from utils.logger import get_logger
from voice.ux.models import AssistantStatus

logger = get_logger(__name__)


class StatusManager:
    """Tracks voice status changes and notifies registered listener delegates."""

    def __init__(
        self, initial_status: AssistantStatus = AssistantStatus.SLEEPING
    ) -> None:
        """Initializes the StatusManager.

        Args:
            initial_status: The starting status state (default SLEEPING).
        """
        self._status = initial_status
        self._listeners: List[Callable[[AssistantStatus, AssistantStatus], None]] = []
        self._lock = threading.Lock()

    @property
    def status(self) -> AssistantStatus:
        """Gets the current AssistantStatus thread-safely."""
        with self._lock:
            return self._status

    @status.setter
    def status(self, new_status: AssistantStatus) -> None:
        """Sets the current status and notifies all transition listeners.

        Args:
            new_status: The target AssistantStatus state.
        """
        old_status = None
        listeners_to_notify = []

        with self._lock:
            if self._status == new_status:
                return
            old_status = self._status
            self._status = new_status
            logger.info("UX Status Transition: %s -> %s", old_status.name, new_status.name)
            # Copy listeners list to avoid modifying during notification iteration
            listeners_to_notify = list(self._listeners)

        # Execute callbacks outside the lock to prevent deadlocks
        for listener in listeners_to_notify:
            try:
                listener(old_status, new_status)
            except Exception as e:
                logger.error("Error in status change listener callback: %s", e)

    def register_listener(
        self, callback: Callable[[AssistantStatus, AssistantStatus], None]
    ) -> None:
        """Registers a callback to receive status change notifications.

        Args:
            callback: Listener function matching signature: (old_status, new_status) -> None.
        """
        with self._lock:
            if callback not in self._listeners:
                logger.debug("Registering status change listener: %s", callback)
                self._listeners.append(callback)

    def unregister_listener(
        self, callback: Callable[[AssistantStatus, AssistantStatus], None]
    ) -> None:
        """Unregisters a previously added status change listener.

        Args:
            callback: The listener function to remove.
        """
        with self._lock:
            if callback in self._listeners:
                logger.debug("Unregistering status change listener: %s", callback)
                self._listeners.remove(callback)
                
    def clear_listeners(self) -> None:
        """Removes all registered status change listeners."""
        with self._lock:
            self._listeners.clear()
