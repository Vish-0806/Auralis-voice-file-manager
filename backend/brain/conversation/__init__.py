"""Conversation package for managing session state, turns, context windows, reference resolution, summaries, recovery, and runtime coordination."""

from brain.conversation.context_manager import (
    ConversationContext,
    ConversationContextConfig,
    ConversationContextManager,
)
from brain.conversation.conversation_session import (
    ConversationSession,
    ConversationSessionConfig,
    ConversationSessionManager,
    ConversationSessionStatus,
    ConversationTurn,
)
from brain.conversation.recovery import (
    ConversationRecoveryConfig,
    ConversationRecoveryManager,
    ConversationRecoveryRecord,
    ConversationRecoveryStatus,
)
from brain.conversation.reference_resolver import (
    ConversationReferenceResolver,
    ReferenceCandidate,
    ReferenceResolutionResult,
    ReferenceResolverConfig,
    ReferenceType,
)
from brain.conversation.runtime import (
    ConversationRuntimeCoordinator,
    get_conversation_runtime,
    reset_conversation_runtime,
)
from brain.conversation.summarizer import (
    ConversationSummarizer,
    ConversationSummary,
    ConversationSummaryConfig,
)

__all__ = [
    "ConversationSessionStatus",
    "ConversationTurn",
    "ConversationSession",
    "ConversationSessionConfig",
    "ConversationSessionManager",
    "ConversationContext",
    "ConversationContextConfig",
    "ConversationContextManager",
    "ReferenceType",
    "ReferenceCandidate",
    "ReferenceResolutionResult",
    "ReferenceResolverConfig",
    "ConversationReferenceResolver",
    "ConversationSummary",
    "ConversationSummaryConfig",
    "ConversationSummarizer",
    "ConversationRecoveryStatus",
    "ConversationRecoveryRecord",
    "ConversationRecoveryConfig",
    "ConversationRecoveryManager",
    "ConversationRuntimeCoordinator",
    "get_conversation_runtime",
    "reset_conversation_runtime",
]
