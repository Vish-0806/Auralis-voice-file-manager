"""Centralized memory configuration module.

Defines the settings schema for the memory subsystem using Pydantic,
enabling configuration via environment variables with safe defaults.
"""

import os
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class MemorySettings(BaseModel):
    """Centralized configuration settings for the Memory subsystem.

    Attributes:
        provider_type: Type of storage provider to use (e.g. "in_memory", "postgres").
        embedding_dimension: Size of semantic embedding vectors. Defaults to 1536.
        cache_ttl_seconds: Cache validity duration in seconds. Defaults to 300.
        similarity_threshold: Default score boundary for vector search matching.
        db_connection_uri: Optional database connection string for future persistent storage.
    """

    provider_type: str = Field(
        default="in_memory",
        description="Memory storage provider type (e.g., 'in_memory', 'postgres')",
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Dimension of semantic embeddings",
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Time to live for memory cache in seconds",
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Similarity threshold for vector search",
    )
    db_connection_uri: Optional[str] = Field(
        default=None,
        description="Connection string for future persistent storage database",
    )


# Globally accessible memory configuration instance
settings = MemorySettings(
    provider_type=os.getenv("AURALIS_MEMORY_PROVIDER", "in_memory"),
    db_connection_uri=os.getenv("AURALIS_MEMORY_DB_URI", None),
)
