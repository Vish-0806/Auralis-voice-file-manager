"""
Module: backend.memory.models

Responsibility:
    Defines the structured data models representing memory units and vectors.
    Enforces type safety for storage payloads.

This module SHOULD:
    - Declare MemoryEntry structures containing metadata (id, tags, content, timestamp).
    - Declare a SemanticVector representation holding vector dimensions and text chunks.
    - Provide configurations models for preferences, directories, and automations.

This module should NEVER:
    - Include persistence, file writing, or database query logic.
    - Reference specific SQL schemas or table layouts.
    - Import database connection clients.
"""

from typing import Dict, Any, List, Optional
import time
import uuid


class MemoryEntry:
    """Represents a structured unit of information stored in relational tables."""
    
    def __init__(self,
                 content: Any,
                 category: str,
                 tags: Optional[List[str]] = None,
                 key: Optional[str] = None) -> None:
        self.key: str = key or str(uuid.uuid4())
        self.content: Any = content
        self.category: str = category
        self.tags: List[str] = tags or []
        self.created_at: float = time.time()


class SemanticVector:
    """Represents a vector embedding and its associated text metadata."""
    
    def __init__(self,
                 embeddings: List[float],
                 text_content: str,
                 metadata: Optional[Dict[str, Any]] = None,
                 vector_id: Optional[str] = None) -> None:
        self.vector_id: str = vector_id or str(uuid.uuid4())
        self.embeddings: List[float] = embeddings
        self.text_content: str = text_content
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: float = time.time()


class UserPreference:
    """Represents a key-value setting profile entry."""
    
    def __init__(self, key: str, value: Any, category: str) -> None:
        self.key: str = key
        self.value: Any = value
        self.category: str = category
        self.updated_at: float = time.time()
