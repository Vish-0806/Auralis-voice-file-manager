"""Context Awareness subsystem.

Exposes context models, temporary memories, reference resolvers, and the
ContextManager to maintain session state and resolve pronouns/ordinals.
"""

from voice.context.models import ContextState, ResolutionResult
from voice.context.memory import TemporaryMemory
from voice.context.reference_resolver import ReferenceResolver
from voice.context.context_manager import ContextManager

__all__ = [
    "ContextState",
    "ResolutionResult",
    "TemporaryMemory",
    "ReferenceResolver",
    "ContextManager",
]
