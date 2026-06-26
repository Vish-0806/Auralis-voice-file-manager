"""
Module: backend.events.registry

Responsibility:
    Tracks active subscriptions mapping event topics to subscribers.
    Provides pattern matching (e.g. wildcard targets like "voice.*") for event routing.

This module SHOULD:
    - Define a SubscriptionRegistry class implementing the IEventRegistry interface.
    - Implement thread-safe dictionary structures to store subscriptions.
    - Support wildcard topic matching (e.g., matching "voice.speech_completed" to "voice.*").

This module should NEVER:
    - Dispatch events or run queues directly.
    - Reference specific configuration files.
    - Block callers during registration operations.
"""

from typing import Dict, Any, List, Optional, Set
import threading
from events.interfaces import IEventRegistry, IEventSubscriber
from events.models import Subscription


class SubscriptionRegistry(IEventRegistry):
    """Tracks active subscriptions, protecting mappings thread-safely."""
    
    def __init__(self) -> None:
        self._subscriptions: Dict[str, Set[IEventSubscriber]] = {}
        self._lock: threading.Lock = threading.Lock()

    def register_subscription(self, subscription: Subscription) -> None:
        """Registers a subscriber for a specific topic pattern."""
        pass

    def remove_subscription(self, subscriber_id: str, topic: str) -> None:
        """Removes a registered subscriber from a topic pattern."""
        pass

    def get_subscribers_for_topic(self, topic: str) -> List[IEventSubscriber]:
        """Queries the registry for subscribers matching the topic pattern (including wildcards)."""
        pass
