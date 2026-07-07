"""Defines states for voice conversation flow."""

from enum import Enum


class ConversationState(Enum):
    """Voice assistant lifecycle conversation states.

    Attributes:
        SLEEPING: Wake-word engine actively listening, core assistant sleeping.
        LISTENING: Recording voice command from the user.
        PROCESSING: Executing voice instruction and getting the result.
        SPEAKING: Synthesizing response back to the user via Text-to-Speech.
        WAITING_FOR_RESPONSE: Active follow-up listening within an active session.
        ERROR: Exceptional error handling state.
    """

    SLEEPING = "SLEEPING"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    WAITING_FOR_RESPONSE = "WAITING_FOR_RESPONSE"
    ERROR = "ERROR"
