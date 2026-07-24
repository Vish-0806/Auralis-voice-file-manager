"""Memory ranker service for scoring and ordering memories based on relevance context."""

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from memory.models.domain_models import MemoryEntry

logger = logging.getLogger(__name__)


class MemoryRankerConfig(BaseModel):
    """Configuration weights and limits for the MemoryRanker.

    Attributes:
        recency_weight: Weight for how recent the memory is.
        session_weight: Weight for matching session trace identifiers.
        workspace_weight: Weight for matching the active workspace path.
        entity_weight: Weight for overlapping keywords / nouns.
        command_weight: Weight for overlapping command action verbs.
        max_conversations: Maximum conversations to retain in context.
        max_executions: Maximum executions to retain in context.
        importance_weight: Weight for memory type importance.
        frequency_weight: Weight for usage frequency count.
        importance_weights: Configurable importance weights based on MemoryType.
        frequency_k: Saturation parameter for frequency scoring.
        command_synonyms: Synonym mapping configuration.
        command_verbs: List of canonical command verbs.
    """

    recency_weight: float = Field(default=0.2, description="Weight for age recency")
    session_weight: float = Field(default=0.3, description="Weight for session matching")
    workspace_weight: float = Field(default=0.2, description="Weight for workspace matching")
    entity_weight: float = Field(default=0.15, description="Weight for entity overlapping tokens")
    command_weight: float = Field(default=0.15, description="Weight for command action verb matching")
    max_conversations: int = Field(default=5, description="Maximum conversations to load")
    max_executions: int = Field(default=3, description="Maximum executions to load")

    # New configurable ranking parameters
    importance_weight: float = Field(default=0.0, description="Weight for memory type importance")
    frequency_weight: float = Field(default=0.0, description="Weight for usage frequency count")

    importance_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "session": 1.0,
            "conversation": 0.8,
            "activity": 0.7,
            "preference": 0.9,
            "workflow": 0.8,
            "project": 0.8,
            "file": 0.8,
            "long_term": 0.8,
        },
        description="Importance weights for memory types"
    )

    frequency_k: float = Field(
        default=5.0,
        description="Saturation parameter for frequency scoring (BM25 term)"
    )

    command_synonyms: Dict[str, str] = Field(
        default_factory=lambda: {
            "remove": "delete",
            "erase": "delete",
            "trash": "delete",
            "destroy": "delete",
            "discard": "delete",
            "deleted": "delete",
            "removing": "delete",
            "make": "create",
            "generate": "create",
            "build": "create",
            "new": "create",
            "created": "create",
            "generating": "create",
            "transfer": "move",
            "relocate": "move",
            "shift": "move",
            "moved": "move",
            "moving": "move",
            "launch": "open",
            "start": "open",
            "run": "open",
            "opened": "open",
            "launching": "open",
        },
        description="Mappings of command synonyms to canonical command verbs"
    )

    command_verbs: List[str] = Field(
        default_factory=lambda: [
            "open",
            "close",
            "launch",
            "mute",
            "unmute",
            "list",
            "delete",
            "create",
            "move",
            "copy",
            "organize",
        ],
        description="Canonical command verbs list"
    )


class MemoryRanker:
    """Service that computes relevance scores for memory entries using heuristic weights."""

    def __init__(self, config: Optional[MemoryRankerConfig] = None) -> None:
        """Initializes the MemoryRanker.

        Args:
            config: Optional MemoryRankerConfig parameters.
        """
        self.config = config or MemoryRankerConfig()

    def _normalize_token(self, token: str) -> str:
        """Normalizes a token by lowercasing and stripping common punctuation.

        Args:
            token: The raw token string.

        Returns:
            The normalized token string.
        """
        return token.lower().strip(".,!?;:\"'`()[]{}<>*_-+/\\")

    def _score_recency(self, entry: MemoryEntry) -> float:
        """Calculates decay score based on the memory creation age.

        Args:
            entry: The MemoryEntry to evaluate.

        Returns:
            Decay score in the range [0.0, 1.0].
        """
        try:
            created_at = entry.metadata.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_seconds = max(0.0, (now - created_at).total_seconds())
            age_hours = age_seconds / 3600.0
            # Exponential decay: score decays to 0.5 in ~14 hours with lambda=0.05
            return math.exp(-0.05 * age_hours)
        except Exception:
            logger.warning("Error calculating memory recency score", exc_info=True)
            return 0.0

    def _score_session(self, entry: MemoryEntry, session_id: Optional[str]) -> float:
        """Checks for direct session ID matching.

        Args:
            entry: The MemoryEntry to evaluate.
            session_id: The active session identifier.

        Returns:
            1.0 if matching, else 0.0.
        """
        if session_id:
            m_sess = entry.metadata.additional_info.get("session_id")
            if m_sess and str(m_sess) == str(session_id):
                return 1.0
        return 0.0

    def _score_workspace(self, entry: MemoryEntry, workspace_path: Optional[str]) -> float:
        """Checks for active workspace directory path matching.

        Args:
            entry: The MemoryEntry to evaluate.
            workspace_path: The active workspace path.

        Returns:
            1.0 if matching, else 0.0.
        """
        if workspace_path:
            path_val = entry.metadata.additional_info.get("workspace_path") or entry.content
            if path_val and isinstance(path_val, str) and path_val.lower() == workspace_path.lower():
                return 1.0
        return 0.0

    def _score_entity_similarity(self, entry: MemoryEntry, query_text: Optional[str]) -> float:
        """Computes overlap similarity for query tokens with a minimum length of 4.

        Args:
            entry: The MemoryEntry to evaluate.
            query_text: The current request message text.

        Returns:
            The Jaccard-style query token overlap score.
        """
        if not query_text:
            return 0.0

        query_words = re.findall(r"\b\w{4,}\b", query_text)
        query_tokens = {self._normalize_token(w) for w in query_words}
        query_tokens = {t for t in query_tokens if t}

        if not query_tokens:
            return 0.0

        content_words = re.findall(r"\b\w{4,}\b", entry.content)
        content_tokens = {self._normalize_token(w) for w in content_words}
        content_tokens = {t for t in content_tokens if t}

        overlap = query_tokens.intersection(content_tokens)
        return len(overlap) / len(query_tokens)

    def _score_command_similarity(self, entry: MemoryEntry, query_text: Optional[str]) -> float:
        """Computes overlap score for command action verbs, supporting synonym expansion.

        Args:
            entry: The MemoryEntry to evaluate.
            query_text: The current request message text.

        Returns:
            Overlap score for command verbs.
        """
        if not query_text:
            return 0.0

        query_words = re.findall(r"\b\w+\b", query_text)
        query_verbs = set()
        for w in query_words:
            norm_w = self._normalize_token(w)
            canonical_w = self.config.command_synonyms.get(norm_w, norm_w)
            if canonical_w in self.config.command_verbs:
                query_verbs.add(canonical_w)

        if not query_verbs:
            return 0.0

        content_words = re.findall(r"\b\w+\b", entry.content)
        content_verbs = set()
        for w in content_words:
            norm_w = self._normalize_token(w)
            canonical_w = self.config.command_synonyms.get(norm_w, norm_w)
            if canonical_w in self.config.command_verbs:
                content_verbs.add(canonical_w)

        overlap = query_verbs.intersection(content_verbs)
        return len(overlap) / len(query_verbs)

    def _score_importance(self, entry: MemoryEntry) -> float:
        """Computes base priority score based on memory entry type.

        Args:
            entry: The MemoryEntry to evaluate.

        Returns:
            Static type importance score in the range [0.0, 1.0].
        """
        type_str = entry.memory_type.value if hasattr(entry.memory_type, "value") else str(entry.memory_type)
        return self.config.importance_weights.get(type_str, 0.5)

    def _score_frequency(self, entry: MemoryEntry) -> float:
        """Applies saturated frequency scoring function for memory usage.

        Args:
            entry: The MemoryEntry to evaluate.

        Returns:
            Bounded frequency score in the range [0.0, 1.0].
        """
        usage_count = entry.metadata.additional_info.get("usage_count")
        if usage_count is None:
            return 0.0
        try:
            val = float(usage_count)
            if val < 0.0:
                return 0.0
            return val / (val + self.config.frequency_k)
        except (ValueError, TypeError):
            return 0.0

    def score_entry(
        self,
        entry: MemoryEntry,
        query_text: Optional[str] = None,
        session_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
    ) -> float:
        """Computes a normalized relevance score from 0.0 to 1.0 for a MemoryEntry.

        Args:
            entry: The MemoryEntry to score.
            query_text: Optional current request message text.
            session_id: Optional current request session/correlation ID.
            workspace_path: Optional current active workspace directory path.

        Returns:
            The computed float score.
        """
        recency_score = self._score_recency(entry)
        session_score = self._score_session(entry, session_id)
        workspace_score = self._score_workspace(entry, workspace_path)
        entity_score = self._score_entity_similarity(entry, query_text)
        command_score = self._score_command_similarity(entry, query_text)
        importance_score = self._score_importance(entry)
        frequency_score = self._score_frequency(entry)

        # Calculate final weighted score
        final_score = (
            self.config.recency_weight * recency_score
            + self.config.session_weight * session_score
            + self.config.workspace_weight * workspace_score
            + self.config.entity_weight * entity_score
            + self.config.command_weight * command_score
            + self.config.importance_weight * importance_score
            + self.config.frequency_weight * frequency_score
        )
        return float(final_score)

    def rank_memories(
        self,
        memories: List[MemoryEntry],
        query_text: Optional[str] = None,
        session_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Scores and ranks a list of MemoryEntry objects in descending order of relevance.

        Args:
            memories: List of MemoryEntry objects.
            query_text: Optional current request message text.
            session_id: Optional current request session/correlation ID.
            workspace_path: Optional current active workspace directory path.

        Returns:
            The sorted list of MemoryEntry objects.
        """
        if not memories:
            return []

        # Sort by relevance score descending
        scored_pairs = [
            (
                self.score_entry(
                    entry,
                    query_text=query_text,
                    session_id=session_id,
                    workspace_path=workspace_path,
                ),
                entry,
            )
            for entry in memories
        ]
        scored_pairs.sort(key=lambda pair: pair[0], reverse=True)
        return [pair[1] for pair in scored_pairs]
