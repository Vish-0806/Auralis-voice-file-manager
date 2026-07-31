"""DefaultEventDispatcher implementation for runtime event recording and notification (Phase 10.7).

Stores structured RuntimeEvent objects internally and dispatches events to registered listeners.
"""

import uuid
import logging
from typing import Any, Callable, Dict, List, Optional

from brain.ai.resilience.interfaces import EventDispatcherInterface
from brain.ai.resilience.resilience_models import EventType, RuntimeEvent

logger = logging.getLogger(__name__)


class DefaultEventDispatcher(EventDispatcherInterface):
    """Stores events and dispatches notifications to registered listeners."""

    def __init__(self) -> None:
        self._events: List[RuntimeEvent] = []
        self._listeners: Dict[EventType, List[Callable[[RuntimeEvent], None]]] = {}

    def dispatch_event(
        self,
        event_type: EventType,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RuntimeEvent:
        """Record and dispatch a structured RuntimeEvent.

        Args:
            event_type: Category EventType enum value.
            source: Name or ID of event source component.
            payload: Optional contextual metadata dict.

        Returns:
            Constructed RuntimeEvent instance.
        """
        event_id = f"evt-{uuid.uuid4().hex[:8]}"

        event = RuntimeEvent(
            event_id=event_id,
            event_type=event_type,
            source=source,
            payload=payload or {},
        )
        self._events.append(event)
        logger.debug(f"Event dispatched: [{event_type.value}] from '{source}'")

        # Notify registered listeners
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(event)
                except Exception as exc:
                    logger.warning(f"Error in event listener for '{event_type.value}': {exc}")

        return event

    def register_listener(
        self,
        event_type: EventType,
        listener: Callable[[RuntimeEvent], None],
    ) -> None:
        """Register observer callback for an EventType."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def get_events(
        self,
        event_type: Optional[EventType] = None,
    ) -> List[RuntimeEvent]:
        """Retrieve recorded events list, optionally filtered by EventType."""
        if event_type:
            return [e for e in self._events if e.event_type == event_type]
        return list(self._events)
