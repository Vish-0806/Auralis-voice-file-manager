"""Auralis Conversational Intelligence Engine package initialization."""

from .models import DialoguePhase, DialogueState, DialogueTurn, DialogueHistory, PendingClarification
from .persistence import DialoguePersistenceManager
from .state_manager import DialogueStateManager
from .history_manager import DialogueHistoryManager
from .followup_resolver import FollowUpResolver
from .ambiguity_resolver import AmbiguityResolver
from .clarification_manager import ClarificationManager
from .recovery_engine import ContextRecoveryEngine
from .entity_linking import EntityLinkingEngine
from .runtime import ConversationalIntelligenceEngine

__all__ = [
    "DialoguePhase",
    "DialogueState",
    "DialogueTurn",
    "DialogueHistory",
    "PendingClarification",
    "DialoguePersistenceManager",
    "DialogueStateManager",
    "DialogueHistoryManager",
    "FollowUpResolver",
    "AmbiguityResolver",
    "ClarificationManager",
    "ContextRecoveryEngine",
    "EntityLinkingEngine",
    "ConversationalIntelligenceEngine",
]
