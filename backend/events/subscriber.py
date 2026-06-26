"""
Module: backend.events.subscriber

Responsibility:
    Defines helper classes for event subscribers.
    Provides filter mechanics to selectively process relevant messages.

This module SHOULD:
    - Define concrete base classes or helpers that implement IEventSubscriber.
    - Provide topic filter matchers to check matching scopes.
    - Support observer callbacks mapping events to functional targets.

This module should NEVER:
    - Include direct OSAL or capability operations.
    - Reference specific database instances.
    - Block event dispatchers.
"""

from typing import Dict, Any, List, Optional, Callable
from events.interfaces import IEventSubscriber
from events.models import EventEnvelope


class EventSubscriber(IEventSubscriber):
    """Event subscriber routing matched events to registered callbacks."""
    
    def __init__(self, subscriber_id: str, callback: Callable[[EventEnvelope], None]) -> None:
        self._subscriber_id: str = subscriber_id
        self.callback: Callable[[EventEnvelope], None] = callback

    @property
    def subscriber_id(self) -> str:
        """Returns the unique identifier of the subscriber."""
        return self._subscriber_id

    def on_event(self, envelope: EventEnvelope) -> None:
        """Triggers the callback when a matching event is received."""
        pass
