"""Abstract Base Class interfaces for the Auralis Intent Resolution Subsystem (Phase 12.2).

Defines canonical interfaces for intent recognizer, entity extractor, intent resolver,
intent validator, intent provider, and intent runtime.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.execution.intent.intent_models import (
    IntentContext,
    IntentEntity,
    IntentHealth,
    IntentResolution,
    ResolutionStatistics,
    UserIntent,
)


class IIntentRecognizer(ABC):
    """Interface for normalizing user text and recognizing structured UserIntent models."""

    @abstractmethod
    def normalize_text(self, text: str) -> str:
        """Normalize raw text by trimming, lowercasing, and removing symbols."""
        pass

    @abstractmethod
    def remove_filler_words(self, text: str) -> str:
        """Strip conversational filler phrases from normalized text."""
        pass

    @abstractmethod
    def recognize(self, text: str) -> UserIntent:
        """Recognize structured UserIntent deterministically without AI calls."""
        pass


class IEntityExtractor(ABC):
    """Interface for extracting structured IntentEntity parameters from raw text."""

    @abstractmethod
    def extract_entities(self, text: str) -> List[IntentEntity]:
        """Extract structured parameter entities (files, paths, apps, dates, etc.)."""
        pass


class IIntentResolver(ABC):
    """Interface for combining recognized intent, extracted entities, and context into an IntentResolution."""

    @abstractmethod
    def resolve(
        self,
        text: str,
        intent: Optional[UserIntent] = None,
        entities: Optional[List[IntentEntity]] = None,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Synthesize primary intent, candidate scores, and ambiguity into an IntentResolution."""
        pass


class IIntentValidator(ABC):
    """Interface for validating resolved intent parameters and generating diagnostics."""

    @abstractmethod
    def validate(
        self,
        resolution: IntentResolution,
        context: Optional[IntentContext] = None,
    ) -> List[str]:
        """Validate resolution for missing parameters, conflicts, or dangerous actions."""
        pass


class IIntentProvider(ABC):
    """Interface for the aggregate Intent Resolution Provider."""

    @abstractmethod
    def resolve_intent(
        self,
        text: str,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Top-level entry point resolving user text end-to-end."""
        pass

    @abstractmethod
    def health_check(self) -> IntentHealth:
        """Report overall health of intent provider components."""
        pass

    @abstractmethod
    def get_statistics(self) -> ResolutionStatistics:
        """Return aggregated resolution performance statistics."""
        pass


class IIntentRuntime(ABC):
    """Interface for the thread-safe singleton lifecycle manager."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the intent runtime lifecycle."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down the intent runtime lifecycle."""
        pass

    @abstractmethod
    def process_intent(
        self,
        text: str,
        context: Optional[IntentContext] = None,
    ) -> IntentResolution:
        """Process input text through the intent resolution provider."""
        pass

    @abstractmethod
    def health_check(self) -> IntentHealth:
        """Fetch real-time health diagnostic status."""
        pass

    @abstractmethod
    def get_statistics(self) -> ResolutionStatistics:
        """Fetch snapshot of resolution statistics."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Reset resolution statistics and clear transient session state."""
        pass
