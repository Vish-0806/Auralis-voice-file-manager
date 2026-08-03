"""Dialogue Management Subsystem for Auralis (Phase 13.3).

Provides dialogue session management, turn registration, dialogue flow state transitions,
policy evaluations, clarification/confirmation detection, and context updates.
"""

from brain.assistant.dialogue.dialogue_manager import DialogueManager
from brain.assistant.dialogue.dialogue_provider import DialogueProvider
from brain.assistant.dialogue.dialogue_runtime import DialogueRuntime
from brain.assistant.dialogue.exceptions import (
    DialogueException,
    DialoguePolicyError,
    DialogueSessionError,
    DialogueStateError,
    DialogueValidationError,
)
from brain.assistant.dialogue.interfaces import (
    IDialogueManager,
    IDialoguePolicyManager,
    IDialogueProvider,
    IDialogueRuntime,
    IDialogueStateManager,
)
from brain.assistant.dialogue.models import (
    DialogueAction,
    DialogueContext,
    DialogueDecision,
    DialogueHealth,
    DialogueMode,
    DialoguePolicy,
    DialogueSession,
    DialogueState,
    DialogueStatistics,
    DialogueStatus,
    DialogueTurn,
)
from brain.assistant.dialogue.policy_manager import PolicyManager
from brain.assistant.dialogue.runtime import (
    get_dialogue_runtime,
    reset_dialogue_runtime,
)
from brain.assistant.dialogue.state_manager import StateManager

__all__ = [
    # Enums & Models
    "DialogueStatus",
    "DialogueAction",
    "DialogueMode",
    "DialogueContext",
    "DialogueTurn",
    "DialogueState",
    "DialoguePolicy",
    "DialogueDecision",
    "DialogueSession",
    "DialogueStatistics",
    "DialogueHealth",
    # Exceptions
    "DialogueException",
    "DialogueStateError",
    "DialoguePolicyError",
    "DialogueValidationError",
    "DialogueSessionError",
    # Interfaces
    "IDialogueManager",
    "IDialoguePolicyManager",
    "IDialogueStateManager",
    "IDialogueProvider",
    "IDialogueRuntime",
    # Managers & Provider
    "DialogueManager",
    "PolicyManager",
    "StateManager",
    "DialogueProvider",
    "DialogueRuntime",
    # Singleton accessors
    "get_dialogue_runtime",
    "reset_dialogue_runtime",
]
