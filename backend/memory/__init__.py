"""Auralis Backend Module: Tiered Memory System.

This module exposes the unified public service layer (MemoryService)
and key domain models for Auralis subsystems.
"""

from memory.manager.memory_service import MemoryService
from memory.models.domain_models import (
    MemoryEntry,
    MemoryMetadata,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)

__all__ = [
    "MemoryService",
    "MemoryEntry",
    "MemoryMetadata",
    "MemoryQuery",
    "MemoryResult",
    "MemoryType",
]
