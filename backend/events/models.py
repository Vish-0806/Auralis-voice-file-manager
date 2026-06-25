"""
Module: backend.events.models

Responsibility:
    Defines data models representing event envelopes and subscriptions.
    Provides immutable structures to guarantee event data safety.

This module SHOULD:
    - Declare an EventEnvelope class containing event metadata (ID, sender, type, timestamp) and payload.
    - Declare a Subscription class mapping a subscriber instance to a topic name.
    - Provide serialization options (to_dict) for logs or IPC communication.

This module should NEVER:
    - Include logic to run queues or thread workers.
    - Reference specific database or configuration schemas.
    - Store active connections.
"""

from typing import Dict, Any, List, Optional
import time
import uuid


class EventEnvelope:
    """Wrapper that packages event payloads with routing metadata."""
    
    def __init__(self,
                 event_type: str,
                 sender: str,
                 payload: Dict[str, Any],
                 correlation_id: Optional[str] = None) -> None:
        self.event_id: str = str(uuid.uuid4())
        self.event_type: str = event_type
        self.sender: str = sender
        self.payload: Dict[str, Any] = payload
        self.timestamp: float = time.time()
        self.correlation_id: str = correlation_id or str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the event envelope metadata and payload into a flat dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "sender": self.sender,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }


class Subscription:
    """Represents a registered topic subscription mapping to an abstract subscriber."""
    
    def __init__(self, topic: str, subscriber: Any) -> None:
        self.subscription_id: str = str(uuid.uuid4())
        self.topic: str = topic
        self.subscriber: Any = subscriber  # Should implement IEventSubscriber
        self.created_at: float = time.time()
