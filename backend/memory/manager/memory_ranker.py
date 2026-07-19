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
    """

    recency_weight: float = Field(default=0.2, description="Weight for age recency")
    session_weight: float = Field(default=0.3, description="Weight for session matching")
    workspace_weight: float = Field(default=0.2, description="Weight for workspace matching")
    entity_weight: float = Field(default=0.15, description="Weight for entity overlapping tokens")
    command_weight: float = Field(default=0.15, description="Weight for command action verb matching")
    max_conversations: int = Field(default=5, description="Maximum conversations to load")
    max_executions: int = Field(default=3, description="Maximum executions to load")


class MemoryRanker:
    """Service that computes relevance scores for memory entries using heuristic weights."""

    def __init__(self, config: Optional[MemoryRankerConfig] = None) -> None:
        """Initializes the MemoryRanker.

        Args:
            config: Optional MemoryRankerConfig parameters.
        """
        self.config = config or MemoryRankerConfig()

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
        # 1. Recency Score
        try:
            created_at = entry.metadata.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_seconds = max(0.0, (now - created_at).total_seconds())
            age_hours = age_seconds / 3600.0
            # Exponential decay: score decays to 0.5 in ~14 hours with lambda=0.05
            recency_score = math.exp(-0.05 * age_hours)
        except Exception:
            logger.warning("Error calculating memory recency score", exc_info=True)
            recency_score = 0.0

        # 2. Session Score
        session_score = 0.0
        if session_id:
            m_sess = entry.metadata.additional_info.get("session_id")
            if m_sess and str(m_sess) == str(session_id):
                session_score = 1.0

        # 3. Workspace Score
        workspace_score = 0.0
        if workspace_path:
            path_val = entry.metadata.additional_info.get("workspace_path") or entry.content
            if path_val and isinstance(path_val, str) and path_val.lower() == workspace_path.lower():
                workspace_score = 1.0

        # 4. Entity Token Overlap Score
        entity_score = 0.0
        if query_text:
            query_tokens = {w.lower() for w in re.findall(r"\b\w{4,}\b", query_text)}
            if query_tokens:
                content_tokens = {w.lower() for w in re.findall(r"\b\w{4,}\b", entry.content)}
                overlap = query_tokens.intersection(content_tokens)
                entity_score = len(overlap) / len(query_tokens)

        # 5. Command Action Verb Overlap Score
        command_score = 0.0
        if query_text:
            command_verbs = {
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
            }
            query_verbs = {
                w.lower()
                for w in re.findall(r"\b\w+\b", query_text)
                if w.lower() in command_verbs
            }
            if query_verbs:
                content_verbs = {
                    w.lower()
                    for w in re.findall(r"\b\w+\b", entry.content)
                    if w.lower() in command_verbs
                }
                overlap = query_verbs.intersection(content_verbs)
                command_score = len(overlap) / len(query_verbs)

        # Calculate final weighted score
        final_score = (
            self.config.recency_weight * recency_score
            + self.config.session_weight * session_score
            + self.config.workspace_weight * workspace_score
            + self.config.entity_weight * entity_score
            + self.config.command_weight * command_score
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
