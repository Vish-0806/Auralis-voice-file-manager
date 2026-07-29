"""Conversation Summarizer for generating deterministic, structured summaries from conversation turns.

This module provides thread-safe summary generation and storage without calling any LLM,
performing reasoning, executing commands, modifying session state, or resolving references.
"""

from datetime import datetime, timezone
import logging
import re
import threading
from typing import Any, Dict, List, Optional, Set
import uuid

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.conversation.conversation_session import ConversationTurn

logger = logging.getLogger(__name__)


class ConversationSummary(BaseModel):
    """Immutable model representing a structured summary of conversation turns."""

    model_config = ConfigDict(frozen=True)

    summary_id: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary_level: int = 1
    total_turns: int = 0
    covered_turns: int = 0
    key_entities: List[str] = Field(default_factory=list)
    key_topics: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    open_items: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSummaryConfig(BaseModel):
    """Configuration options for ConversationSummarizer limits and triggers."""

    summary_trigger_turns: int = 25
    maximum_summary_levels: int = 10
    maximum_entities: int = 100
    maximum_topics: int = 100
    maximum_open_items: int = 100
    maximum_decisions: int = 100


class ConversationSummarizer:
    """Thread-safe engine for generating, storing, updating, and merging structured conversation summaries."""

    def __init__(self, config: Optional[ConversationSummaryConfig] = None) -> None:
        """Initializes the summarizer with optional configuration and thread lock."""
        self.config = config or ConversationSummaryConfig()
        self._summaries: Dict[str, List[ConversationSummary]] = {}
        self._lock = threading.RLock()

    def summarize_turns(
        self,
        session_id: str,
        turns: List[ConversationTurn],
        summary_level: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationSummary:
        """Deterministically extracts structured entities, topics, decisions, and open items from turns."""
        raw_entities: List[str] = []
        raw_topics: List[str] = []
        raw_decisions: List[str] = []
        raw_open_items: List[str] = []

        for turn in turns:
            meta = turn.metadata or {}
            content = turn.content or ""

            # 1. Entity extraction
            if "entities" in meta:
                ents = meta["entities"]
                if isinstance(ents, list):
                    raw_entities.extend(str(e) for e in ents)
                else:
                    raw_entities.append(str(ents))
            if "entity" in meta:
                raw_entities.append(str(meta["entity"]))
            if "filename" in meta:
                raw_entities.append(str(meta["filename"]))
            if "path" in meta:
                raw_entities.append(str(meta["path"]))

            # Extract quoted strings or file references from content
            quoted = re.findall(r'["\']([^"\']+)["\']', content)
            raw_entities.extend(quoted)
            file_refs = re.findall(r"\b[\w\-]+\.[a-zA-Z0-9]{2,4}\b", content)
            raw_entities.extend(file_refs)

            # 2. Topic extraction
            if "topics" in meta:
                top = meta["topics"]
                if isinstance(top, list):
                    raw_topics.extend(str(t) for t in top)
                else:
                    raw_topics.append(str(top))
            if "topic" in meta:
                raw_topics.append(str(meta["topic"]))
            if "intent" in meta:
                raw_topics.append(str(meta["intent"]))
            if "action" in meta:
                raw_topics.append(str(meta["action"]))

            # Topic patterns in content
            content_lower = content.lower()
            if any(k in content_lower for k in ["move", "moving", "transfer"]):
                raw_topics.append("move file")
            if any(k in content_lower for k in ["rename", "renaming"]):
                raw_topics.append("rename folder")
            if any(k in content_lower for k in ["delete", "remove"]):
                raw_topics.append("delete item")
            if any(k in content_lower for k in ["organize", "sorting"]):
                raw_topics.append("organize files")

            # 3. Decision extraction
            if "decisions" in meta:
                decs = meta["decisions"]
                if isinstance(decs, list):
                    raw_decisions.extend(str(d) for d in decs)
                else:
                    raw_decisions.append(str(decs))
            if "decision" in meta:
                raw_decisions.append(str(meta["decision"]))

            if any(k in content_lower for k in ["destination folder selected", "selected destination", "decision confirmed", "user selected"]):
                raw_decisions.append("destination folder selected")
            elif "confirmed" in content_lower:
                raw_decisions.append("user confirmation received")
            elif "approved" in content_lower:
                raw_decisions.append("action approved")

            # 4. Open Item extraction
            if "open_items" in meta:
                items = meta["open_items"]
                if isinstance(items, list):
                    raw_open_items.extend(str(i) for i in items)
                else:
                    raw_open_items.append(str(items))
            if "open_item" in meta:
                raw_open_items.append(str(meta["open_item"]))

            if "awaiting user confirmation" in content_lower or "awaiting confirmation" in content_lower:
                raw_open_items.append("awaiting user confirmation")
            elif "pending" in content_lower:
                raw_open_items.append("pending user input")
            elif content.strip().endswith("?"):
                raw_open_items.append("awaiting response to query")

        key_entities = self._combine_unique([], raw_entities, self.config.maximum_entities)
        key_topics = self._combine_unique([], raw_topics, self.config.maximum_topics)
        decisions = self._combine_unique([], raw_decisions, self.config.maximum_decisions)
        open_items = self._combine_unique([], raw_open_items, self.config.maximum_open_items)

        sid = f"summary_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        return ConversationSummary(
            summary_id=sid,
            session_id=session_id,
            created_at=now,
            updated_at=now,
            summary_level=summary_level,
            total_turns=len(turns),
            covered_turns=len(turns),
            key_entities=key_entities,
            key_topics=key_topics,
            decisions=decisions,
            open_items=open_items,
            metadata=metadata or {},
        )

    def create_summary(
        self,
        session_id: str,
        turns: List[ConversationTurn],
        summary_level: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationSummary:
        """Creates and registers a structured summary for a session."""
        with self._lock:
            summary = self.summarize_turns(
                session_id=session_id,
                turns=turns,
                summary_level=summary_level,
                metadata=metadata,
            )

            if session_id not in self._summaries:
                self._summaries[session_id] = []
            self._summaries[session_id].append(summary)

            logger.info("Conversation Summary Created: summary_id=%s, session_id=%s", summary.summary_id, session_id)
            return summary

    def get_summary(
        self,
        session_id: str,
        summary_id: Optional[str] = None,
    ) -> Optional[ConversationSummary]:
        """Retrieves a summary by session_id and optional summary_id without throwing exceptions."""
        with self._lock:
            s_list = self._summaries.get(session_id, [])
            if not s_list:
                return None

            if summary_id is not None:
                for s in s_list:
                    if s.summary_id == summary_id:
                        return s
                return None

            return s_list[-1]

    def update_summary(
        self,
        session_id: str,
        new_turns: List[ConversationTurn],
        summary_id: Optional[str] = None,
    ) -> Optional[ConversationSummary]:
        """Incrementally extends an existing summary with new turns without losing prior data."""
        with self._lock:
            existing = self.get_summary(session_id, summary_id)
            if existing is None:
                return None

            delta_summary = self.summarize_turns(session_id, new_turns, summary_level=existing.summary_level)

            merged_entities = self._combine_unique(existing.key_entities, delta_summary.key_entities, self.config.maximum_entities)
            merged_topics = self._combine_unique(existing.key_topics, delta_summary.key_topics, self.config.maximum_topics)
            merged_decisions = self._combine_unique(existing.decisions, delta_summary.decisions, self.config.maximum_decisions)
            merged_open_items = self._combine_unique(existing.open_items, delta_summary.open_items, self.config.maximum_open_items)

            now = datetime.now(timezone.utc)
            updated = ConversationSummary(
                summary_id=existing.summary_id,
                session_id=session_id,
                created_at=existing.created_at,
                updated_at=now,
                summary_level=existing.summary_level,
                total_turns=existing.total_turns + len(new_turns),
                covered_turns=existing.covered_turns + len(new_turns),
                key_entities=merged_entities,
                key_topics=merged_topics,
                decisions=merged_decisions,
                open_items=merged_open_items,
                metadata=existing.metadata,
            )

            # Update in store
            s_list = self._summaries[session_id]
            for i, s in enumerate(s_list):
                if s.summary_id == existing.summary_id:
                    s_list[i] = updated
                    break

            logger.info("Conversation Summary Updated: summary_id=%s, session_id=%s", existing.summary_id, session_id)
            return updated

    def merge_summaries(
        self,
        summary1: ConversationSummary,
        summary2: ConversationSummary,
    ) -> ConversationSummary:
        """Combines two structured summaries into a higher-level summary."""
        with self._lock:
            new_level = min(max(summary1.summary_level, summary2.summary_level) + 1, self.config.maximum_summary_levels)
            merged_entities = self._combine_unique(summary1.key_entities, summary2.key_entities, self.config.maximum_entities)
            merged_topics = self._combine_unique(summary1.key_topics, summary2.key_topics, self.config.maximum_topics)
            merged_decisions = self._combine_unique(summary1.decisions, summary2.decisions, self.config.maximum_decisions)
            merged_open_items = self._combine_unique(summary1.open_items, summary2.open_items, self.config.maximum_open_items)

            now = datetime.now(timezone.utc)
            merged_meta = {**summary1.metadata, **summary2.metadata}

            merged = ConversationSummary(
                summary_id=f"summary_{uuid.uuid4().hex[:12]}",
                session_id=summary1.session_id,
                created_at=now,
                updated_at=now,
                summary_level=new_level,
                total_turns=summary1.total_turns + summary2.total_turns,
                covered_turns=summary1.covered_turns + summary2.covered_turns,
                key_entities=merged_entities,
                key_topics=merged_topics,
                decisions=merged_decisions,
                open_items=merged_open_items,
                metadata=merged_meta,
            )

            if summary1.session_id not in self._summaries:
                self._summaries[summary1.session_id] = []
            self._summaries[summary1.session_id].append(merged)

            logger.info("Conversation Summaries Merged: summary1_id=%s, summary2_id=%s", summary1.summary_id, summary2.summary_id)
            return merged

    def list_summaries(self, session_id: Optional[str] = None) -> List[ConversationSummary]:
        """Lists summaries stored for a session, or all stored summaries if session_id is None."""
        with self._lock:
            if session_id is not None:
                return list(self._summaries.get(session_id, []))

            all_summaries: List[ConversationSummary] = []
            for s_list in self._summaries.values():
                all_summaries.extend(s_list)
            return all_summaries

    def remove_summary(self, summary_id: str) -> bool:
        """Removes a summary entry by summary_id."""
        with self._lock:
            for sid, s_list in list(self._summaries.items()):
                for i, s in enumerate(s_list):
                    if s.summary_id == summary_id:
                        s_list.pop(i)
                        if not s_list:
                            del self._summaries[sid]
                        logger.info("Conversation Summary Removed: summary_id=%s", summary_id)
                        return True
            return False

    def clear(self) -> None:
        """Clears all stored summaries."""
        with self._lock:
            self._summaries.clear()
            logger.info("Conversation Summarizer Cleared")

    def _combine_unique(self, list1: List[str], list2: List[str], max_limit: int) -> List[str]:
        """Internal helper to combine strings while preserving chronological order and removing duplicates."""
        result: List[str] = []
        seen: Set[str] = set()

        for item in list1 + list2:
            clean_item = str(item).strip()
            if clean_item and clean_item not in seen:
                seen.add(clean_item)
                result.append(clean_item)
                if len(result) >= max_limit:
                    break

        return result
