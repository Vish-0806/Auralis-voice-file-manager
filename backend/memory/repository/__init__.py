"""Repository package initialization.

Exposes the RepositoryFactory and all concrete, specialized repositories
representing the database-specific data access objects.
"""

from memory.repository.base_repository import BaseRepository
from memory.repository.user_repository import UserRepository
from memory.repository.preference_repository import PreferenceRepository
from memory.repository.workspace_repository import WorkspaceRepository
from memory.repository.context_repository import ContextRepository
from memory.repository.conversation_repository import ConversationRepository
from memory.repository.routine_repository import RoutineRepository
from memory.repository.execution_repository import ExecutionRepository
from memory.repository.memory_event_repository import MemoryEventRepository
from memory.repository.repository_factory import RepositoryFactory

__all__ = [
    "BaseRepository",
    "UserRepository",
    "PreferenceRepository",
    "WorkspaceRepository",
    "ContextRepository",
    "ConversationRepository",
    "RoutineRepository",
    "ExecutionRepository",
    "MemoryEventRepository",
    "RepositoryFactory",
]
