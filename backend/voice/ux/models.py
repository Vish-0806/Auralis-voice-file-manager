"""Defines data models, enums, and structures for Voice UX feedback."""

from dataclasses import dataclass, field
from enum import Enum
import time


class AssistantStatus(Enum):
    """Voice Assistant UX status states.

    Attributes:
        SLEEPING: Wake-word engine actively listening, core assistant sleeping.
        WAKE_DETECTED: Wake word was just matched, triggering activation chimes.
        LISTENING: Recording user voice command.
        PROCESSING: Assistant/File Capability executing instruction.
        SPEAKING: Text-to-Speech active.
        WAITING: Awaiting consecutive command in active session.
        ERROR: Failure or timeout state.
    """

    SLEEPING = "SLEEPING"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    WAITING = "WAITING"
    ERROR = "ERROR"


@dataclass
class UXNotification:
    """Encloses a status notification update.

    Attributes:
        status: The related AssistantStatus state.
        message: The descriptive plain text notification string.
        timestamp: Epoch timestamp when the notification occurred.
    """

    status: AssistantStatus
    message: str
    timestamp: float = field(default_factory=time.time)
