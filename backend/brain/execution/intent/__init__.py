"""Intent Resolution Engine subsystem package for Auralis (Phase 12.2).

Exports domain models, enums, exceptions, interfaces, recognizer, entity extractor,
resolver, validator, provider, runtime lifecycle manager, and global accessors.
"""

from .entity_extractor import EntityExtractor
from .exceptions import (
    AmbiguousIntentError,
    EntityExtractionError,
    IntentException,
    IntentRecognitionError,
    IntentResolutionError,
)
from .intent_models import (
    AmbiguityLevel,
    EntityType,
    IntentCandidate,
    IntentCategory,
    IntentConfidence,
    IntentContext,
    IntentEntity,
    IntentHealth,
    IntentResolution,
    ResolutionStatistics,
    ResolutionStatus,
    UserIntent,
)
from .intent_provider import IntentProvider
from .intent_recognizer import IntentRecognizer
from .intent_resolver import IntentResolver
from .intent_runtime import IntentRuntime, IntentRuntimeStatus
from .intent_validator import IntentValidator
from .interfaces import (
    IEntityExtractor,
    IIntentProvider,
    IIntentRecognizer,
    IIntentResolver,
    IIntentRuntime,
    IIntentValidator,
)
from .runtime import get_intent_runtime, reset_intent_runtime

__all__ = [
    # Models & Enums
    "IntentCategory",
    "IntentConfidence",
    "ResolutionStatus",
    "EntityType",
    "AmbiguityLevel",
    "UserIntent",
    "IntentEntity",
    "IntentContext",
    "IntentCandidate",
    "IntentResolution",
    "ResolutionStatistics",
    "IntentHealth",
    # Exceptions
    "IntentException",
    "IntentRecognitionError",
    "IntentResolutionError",
    "EntityExtractionError",
    "AmbiguousIntentError",
    # Interfaces
    "IEntityExtractor",
    "IIntentProvider",
    "IIntentRecognizer",
    "IIntentResolver",
    "IIntentRuntime",
    "IIntentValidator",
    # Subsystem Core Components
    "IntentRecognizer",
    "EntityExtractor",
    "IntentResolver",
    "IntentValidator",
    "IntentProvider",
    "IntentRuntime",
    "IntentRuntimeStatus",
    # Global Accessors
    "get_intent_runtime",
    "reset_intent_runtime",
]
