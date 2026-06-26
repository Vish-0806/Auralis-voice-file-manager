"""
Module: backend.events.interfaces

Responsibility:
    Defines abstract interface contracts for Auralis Event-Driven Architecture (EDA).
    Enforces decoupling between publishers, subscribers, and the central broker.

This module SHOULD:
    - Declare abstract classes (abc.ABC) representing event buses, publishers, and subscribers.
    - Standardize parameters and type definitions for event routing.
    - Support asynchronous and synchronous event transmission designs.

This module should NEVER:
    - Include concrete event loop runners or thread pool pools.
    - Reference specific capability events or topics.
    - Import external broker client packages (e.g., redis, rabbitmq).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from events.models import EventEnvelope, Subscription


class IEventSubscriber(ABC):
    """Abstract contract for components that handle system events."""
    
    @property
    @abstractmethod
    def subscriber_id(self) -> str:
        """Returns a unique identifier for the subscriber."""
        pass

    @abstractmethod
    def on_event(self, envelope: EventEnvelope) -> None:
        """Invoked asynchronously when a subscribed event is published."""
        pass


class IEventPublisher(ABC):
    """Abstract contract for components that publish system events."""
    
    @abstractmethod
    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Constructs and publishes an event envelope to the broker."""
        pass


class IEventDispatcher(ABC):
    """Abstract contract for asynchronous event queue dispatchers."""
    
    @abstractmethod
    def dispatch(self, envelope: EventEnvelope, subscribers: List[IEventSubscriber]) -> None:
        """Enqueues and dispatches an event to the registered target subscribers."""
        pass


class IEventRegistry(ABC):
    """Abstract contract for managing event topic subscriptions."""
    
    @abstractmethod
    def register_subscription(self, subscription: Subscription) -> None:
        """Registers a subscription matching a topic to a subscriber."""
        pass

    @abstractmethod
    def remove_subscription(self, subscriber_id: str, topic: str) -> None:
        """Removes a registered subscription."""
        pass

    @abstractmethod
    def get_subscribers_for_topic(self, topic: str) -> List[IEventSubscriber]:
        """Retrieves all active subscribers registered for a given topic."""
        pass


class IEventBus(ABC):
    """Abstract contract for the central event broker."""
    
    @abstractmethod
    def publish_envelope(self, envelope: EventEnvelope) -> None:
        """Processes and routes an event envelope through the subscription registry."""
        pass

    @abstractmethod
    def subscribe(self, topic: str, subscriber: IEventSubscriber) -> None:
        """Subscribes a component to a specific event topic or wildcard pattern."""
        pass

    @abstractmethod
    def unsubscribe(self, topic: str, subscriber: IEventSubscriber) -> None:
        """Unsubscribes a component from an event topic."""
        pass
