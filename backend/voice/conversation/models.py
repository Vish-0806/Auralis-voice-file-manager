"""Defines data structures for conversation management."""

from dataclasses import dataclass, field
import time
import uuid
from voice.conversation.conversation_state import ConversationState
from voice.conversation.context import ConversationContext


@dataclass
class ConversationSession:
    """Represents an active voice conversation session.

    Attributes:
        session_id: Universally unique identifier for the session.
        state: The current ConversationState.
        context: Context parameters tracked during the session.
        start_time: Epoch timestamp of when the session was created.
        last_active_time: Epoch timestamp of the last processed activity.
        is_active: Status flag indicating if the session is alive.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ConversationState = ConversationState.SLEEPING
    context: ConversationContext = field(default_factory=ConversationContext)
    start_time: float = field(default_factory=time.time)
    last_active_time: float = field(default_factory=time.time)
    is_active: bool = True
