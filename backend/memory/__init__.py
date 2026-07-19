"""Auralis Backend Module: Tiered Memory System.

This module exposes the unified public service layer (MemoryService)
and key domain models for Auralis subsystems.
"""

from memory.manager.memory_service import MemoryService
from memory.manager.context_builder import ContextBuilder
from memory.preferences.preference_service import PreferenceService
from memory.context.context_service import ContextService
from memory.workspace.workspace_service import WorkspaceService
from memory.learning.routine_learning_service import RoutineLearningService
from memory.personalization.personalization_service import PersonalizationService
from memory.coordinator.memory_coordinator import MemoryCoordinator
from memory.models.domain_models import (
    MemoryEntry,
    MemoryMetadata,
    MemoryQuery,
    MemoryResult,
    MemoryType,
    AssistantContext,
)

__all__ = [
    "MemoryService",
    "ContextBuilder",
    "PreferenceService",
    "ContextService",
    "WorkspaceService",
    "RoutineLearningService",
    "PersonalizationService",
    "MemoryCoordinator",
    "MemoryEntry",
    "MemoryMetadata",
    "MemoryQuery",
    "MemoryResult",
    "MemoryType",
    "AssistantContext",
]
