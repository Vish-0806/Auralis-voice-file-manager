"""Conversation Reference Resolver for resolving conversational references to entities.

This module provides thread-safe reference resolution across pronouns, ordinals,
temporal terms, relative terms, and entity names without performing reasoning,
LLM calls, conversation summarization, or command execution.
"""

from enum import Enum
import logging
import re
import threading
from typing import Any, Dict, List, Optional, Union

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ReferenceType(str, Enum):
    """Enumeration of supported conversational reference types."""

    PRONOUN = "PRONOUN"
    ORDINAL = "ORDINAL"
    TEMPORAL = "TEMPORAL"
    ENTITY = "ENTITY"
    RELATIVE = "RELATIVE"
    UNKNOWN = "UNKNOWN"


class ReferenceCandidate(BaseModel):
    """Immutable model representing a target entity candidate for resolution."""

    model_config = ConfigDict(frozen=True)

    identifier: str
    reference_type: ReferenceType = ReferenceType.ENTITY
    display_name: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReferenceResolutionResult(BaseModel):
    """Immutable model representing the outcome of a reference resolution attempt."""

    model_config = ConfigDict(frozen=True)

    reference: str
    resolved: bool
    confidence: float = 0.0
    candidate: Optional[ReferenceCandidate] = None
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReferenceResolverConfig(BaseModel):
    """Configuration settings for ConversationReferenceResolver limits and thresholds."""

    minimum_confidence: float = 0.50
    maximum_candidates: int = 20
    maximum_reference_history: int = 100


class ConversationReferenceResolver:
    """Thread-safe engine for resolving conversational references based on entity history."""

    PRONOUN_SET = {
        "it", "that", "this", "them", "these", "those", "its", "their", "they", "him", "her"
    }

    ORDINAL_MAP = {
        "first": 0, "1st": 0,
        "second": 1, "2nd": 1,
        "third": 2, "3rd": 2,
        "fourth": 3, "4th": 3,
        "fifth": 4, "5th": 4,
        "last": -1,
        "second to last": -2,
        "penultimate": -2,
    }

    TEMPORAL_SET = {
        "previous", "earlier", "latest", "last", "recent", "most recent"
    }

    RELATIVE_SET = {
        "next", "before", "after", "following"
    }

    def __init__(self, config: Optional[ReferenceResolverConfig] = None) -> None:
        """Initializes the reference resolver with optional configuration and lock."""
        self.config = config or ReferenceResolverConfig()
        self._recent_entities: List[ReferenceCandidate] = []
        self._lock = threading.RLock()

    def register_entity(
        self,
        candidate_or_id: Union[ReferenceCandidate, str],
        display_name: Optional[str] = None,
        reference_type: ReferenceType = ReferenceType.ENTITY,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReferenceCandidate:
        """Registers an entity candidate, maintaining chronological insertion history."""
        with self._lock:
            if isinstance(candidate_or_id, ReferenceCandidate):
                candidate = candidate_or_id
            else:
                candidate = ReferenceCandidate(
                    identifier=candidate_or_id,
                    reference_type=reference_type,
                    display_name=display_name or candidate_or_id,
                    confidence=confidence,
                    metadata=metadata or {},
                )

            # Remove existing candidate with same identifier to move to most recent
            self._recent_entities = [c for c in self._recent_entities if c.identifier != candidate.identifier]
            self._recent_entities.append(candidate)

            # Enforce maximum history limit
            while len(self._recent_entities) > self.config.maximum_reference_history:
                self._recent_entities.pop(0)

            logger.info("Entity Registered: identifier=%s, reference_type=%s", candidate.identifier, candidate.reference_type)
            return candidate

    def register_entities(self, candidates: List[Union[ReferenceCandidate, Dict[str, Any]]]) -> None:
        """Registers multiple entity candidates in sequence."""
        with self._lock:
            for item in candidates:
                if isinstance(item, ReferenceCandidate):
                    self.register_entity(item)
                elif isinstance(item, dict):
                    self.register_entity(**item)

    def resolve_reference(
        self,
        reference_text: str,
        session_id: Optional[str] = None,
    ) -> ReferenceResolutionResult:
        """Dispatches reference resolution to appropriate resolver based on reference classification."""
        with self._lock:
            if not reference_text or not reference_text.strip():
                result = ReferenceResolutionResult(
                    reference=reference_text or "",
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason="Empty reference text",
                )
                logger.info("Reference Resolution Failed: reference=%s, reason=%s", reference_text, result.reason)
                return result

            clean_ref = reference_text.strip().lower()

            # Classify reference category
            if clean_ref in self.PRONOUN_SET:
                result = self.resolve_pronoun(reference_text)
            elif clean_ref in self.ORDINAL_MAP:
                result = self.resolve_ordinal(reference_text)
            elif clean_ref in self.TEMPORAL_SET:
                result = self.resolve_temporal(reference_text)
            elif clean_ref in self.RELATIVE_SET:
                result = self.resolve_relative(reference_text)
            else:
                # Direct or fuzzy entity name matching
                result = self._resolve_entity_name(reference_text)

            if result.resolved and result.confidence >= self.config.minimum_confidence:
                logger.info("Reference Resolved: reference=%s, identifier=%s", reference_text, result.candidate.identifier if result.candidate else "")
            else:
                logger.info("Reference Resolution Failed: reference=%s, reason=%s", reference_text, result.reason)

            return result

    def resolve_pronoun(self, reference_text: str) -> ReferenceResolutionResult:
        """Resolves pronoun references (it, that, this, them, etc.) to recent entity history."""
        with self._lock:
            if not self._recent_entities:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason="No registered entity history for pronoun resolution",
                )

            clean_ref = reference_text.strip().lower()
            # For pronouns like 'it', 'that', 'this', resolve to the most recently registered entity
            candidate = self._recent_entities[-1]
            confidence = min(0.95, candidate.confidence)

            if confidence < self.config.minimum_confidence:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=confidence,
                    candidate=None,
                    reason="Candidate confidence below minimum threshold",
                )

            return ReferenceResolutionResult(
                reference=reference_text,
                resolved=True,
                confidence=confidence,
                candidate=candidate,
                reason=f"Pronoun '{reference_text}' resolved to most recent entity '{candidate.identifier}'",
            )

    def resolve_ordinal(self, reference_text: str) -> ReferenceResolutionResult:
        """Resolves ordinal references (first, second, 1st, last, etc.) by index position."""
        with self._lock:
            clean_ref = reference_text.strip().lower()
            if clean_ref not in self.ORDINAL_MAP:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason=f"Unrecognized ordinal reference '{reference_text}'",
                )

            idx = self.ORDINAL_MAP[clean_ref]
            total = len(self._recent_entities)

            if total == 0:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason="No registered entities available for ordinal resolution",
                )

            # Map index
            target_index = idx if idx >= 0 else total + idx
            if 0 <= target_index < total:
                candidate = self._recent_entities[target_index]
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=1.0,
                    candidate=candidate,
                    reason=f"Ordinal '{reference_text}' resolved to candidate index {target_index}",
                )

            return ReferenceResolutionResult(
                reference=reference_text,
                resolved=False,
                confidence=0.0,
                candidate=None,
                reason=f"Ordinal index {target_index} out of bounds for history size {total}",
            )

    def resolve_temporal(self, reference_text: str) -> ReferenceResolutionResult:
        """Resolves temporal references (previous, earlier, latest, last, recent)."""
        with self._lock:
            clean_ref = reference_text.strip().lower()
            total = len(self._recent_entities)

            if total == 0:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason="No registered entities for temporal resolution",
                )

            if clean_ref in {"latest", "last", "recent", "most recent"}:
                candidate = self._recent_entities[-1]
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=1.0,
                    candidate=candidate,
                    reason=f"Temporal '{reference_text}' resolved to latest entity",
                )

            if clean_ref in {"previous", "earlier"}:
                if total >= 2:
                    candidate = self._recent_entities[-2]
                    return ReferenceResolutionResult(
                        reference=reference_text,
                        resolved=True,
                        confidence=0.90,
                        candidate=candidate,
                        reason=f"Temporal '{reference_text}' resolved to previous entity",
                    )
                elif total == 1:
                    candidate = self._recent_entities[-1]
                    return ReferenceResolutionResult(
                        reference=reference_text,
                        resolved=True,
                        confidence=0.70,
                        candidate=candidate,
                        reason=f"Temporal '{reference_text}' resolved to sole available entity",
                    )

            return ReferenceResolutionResult(
                reference=reference_text,
                resolved=False,
                confidence=0.0,
                candidate=None,
                reason=f"Unresolved temporal reference '{reference_text}'",
            )

    def resolve_relative(self, reference_text: str) -> ReferenceResolutionResult:
        """Resolves relative position references (next, before, after, following)."""
        with self._lock:
            clean_ref = reference_text.strip().lower()
            total = len(self._recent_entities)

            if total == 0:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=False,
                    confidence=0.0,
                    candidate=None,
                    reason="No registered entities for relative resolution",
                )

            if clean_ref in {"next", "after", "following"}:
                candidate = self._recent_entities[-1]
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=0.85,
                    candidate=candidate,
                    reason=f"Relative '{reference_text}' resolved to most recent entity",
                )

            if clean_ref == "before":
                idx = -2 if total >= 2 else -1
                candidate = self._recent_entities[idx]
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=0.85,
                    candidate=candidate,
                    reason=f"Relative '{reference_text}' resolved to prior entity",
                )

            return ReferenceResolutionResult(
                reference=reference_text,
                resolved=False,
                confidence=0.0,
                candidate=None,
                reason=f"Unresolved relative reference '{reference_text}'",
            )

    def remove_entity(self, identifier: str) -> bool:
        """Removes a registered entity by identifier."""
        with self._lock:
            initial_count = len(self._recent_entities)
            self._recent_entities = [c for c in self._recent_entities if c.identifier != identifier]
            removed = len(self._recent_entities) < initial_count

            if removed:
                logger.info("Entity Removed: identifier=%s", identifier)
            return removed

    def clear_history(self) -> None:
        """Clears all registered entity history."""
        with self._lock:
            self._recent_entities.clear()
            logger.info("History Cleared")

    def list_entities(self) -> List[ReferenceCandidate]:
        """Returns copy of currently registered entity candidates in chronological order."""
        with self._lock:
            return list(self._recent_entities)

    def clear(self) -> None:
        """Clears the reference resolver state."""
        with self._lock:
            self._recent_entities.clear()
            logger.info("Reference Resolver Cleared")

    def _resolve_entity_name(self, reference_text: str) -> ReferenceResolutionResult:
        """Internal helper to match reference_text against registered entity names/identifiers."""
        clean_ref = reference_text.strip().lower()

        # Check exact identifier or display name match (reverse search for most recent)
        for candidate in reversed(self._recent_entities):
            if candidate.identifier.lower() == clean_ref or candidate.display_name.lower() == clean_ref:
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=1.0,
                    candidate=candidate,
                    reason="Exact entity identifier/name match",
                )

        # Check partial/substring match
        for candidate in reversed(self._recent_entities):
            if clean_ref in candidate.display_name.lower() or clean_ref in candidate.identifier.lower():
                return ReferenceResolutionResult(
                    reference=reference_text,
                    resolved=True,
                    confidence=0.85,
                    candidate=candidate,
                    reason="Partial entity name match",
                )

        return ReferenceResolutionResult(
            reference=reference_text,
            resolved=False,
            confidence=0.0,
            candidate=None,
            reason=f"No entity matching '{reference_text}' found",
        )
