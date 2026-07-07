"""Routes pipeline events between subsystems asynchronously."""

import threading
from typing import Any, Callable, Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)


class EventRouter:
    """Loosely couples pipeline phases by routing events to registered listeners."""

    def __init__(self) -> None:
        """Initializes the EventRouter with empty subscriber maps."""
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Subscribes a listener to a specific event type.

        Args:
            event_type: The unique event type name.
            callback: The callback function executed when the event triggers.
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            if callback not in self._listeners[event_type]:
                logger.debug("Subscribed callback %s to event '%s'", callback, event_type)
                self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Removes a listener subscription from an event type.

        Args:
            event_type: The event type name.
            callback: The listener callback function to remove.
        """
        with self._lock:
            if event_type in self._listeners and callback in self._listeners[event_type]:
                logger.debug("Unsubscribed callback %s from event '%s'", callback, event_type)
                self._listeners[event_type].remove(callback)

    def publish(self, event_type: str, event_data: Any) -> None:
        """Publishes an event and invokes all registered listener callbacks.

        Args:
            event_type: The unique event identifier.
            event_data: The event payload dictionary or data model.
        """
        logger.debug("Publishing event '%s': %s", event_type, event_data)

        callbacks = []
        with self._lock:
            if event_type in self._listeners:
                callbacks = list(self._listeners[event_type])

        for callback in callbacks:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(
                    "Error in callback for event '%s': %s",
                    event_type,
                    e,
                )
