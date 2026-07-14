"""Repository factory module for Auralis."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.repository.user_repository import UserRepository
from memory.repository.preference_repository import PreferenceRepository
from memory.repository.workspace_repository import WorkspaceRepository
from memory.repository.context_repository import ContextRepository
from memory.repository.conversation_repository import ConversationRepository
from memory.repository.routine_repository import RoutineRepository
from memory.repository.execution_repository import ExecutionRepository
from memory.repository.memory_event_repository import MemoryEventRepository


class RepositoryFactory:
    """Factory for resolving and instantiating memory database repositories.

    Designed to support dependency injection and context lifecycle sessions.
    """

    def __init__(self, db: Session) -> None:
        """Initializes the RepositoryFactory with a database session.

        Args:
            db: The active SQLAlchemy database Session.
        """
        self._db = db

    def get_user_repository(self) -> UserRepository:
        """Resolves UserRepository."""
        return UserRepository(self._db)

    def get_preference_repository(self) -> PreferenceRepository:
        """Resolves PreferenceRepository."""
        return PreferenceRepository(self._db)

    def get_workspace_repository(self) -> WorkspaceRepository:
        """Resolves WorkspaceRepository."""
        return WorkspaceRepository(self._db)

    def get_context_repository(self) -> ContextRepository:
        """Resolves ContextRepository."""
        return ContextRepository(self._db)

    def get_conversation_repository(self) -> ConversationRepository:
        """Resolves ConversationRepository."""
        return ConversationRepository(self._db)

    def get_routine_repository(self) -> RoutineRepository:
        """Resolves RoutineRepository."""
        return RoutineRepository(self._db)

    def get_execution_repository(self) -> ExecutionRepository:
        """Resolves ExecutionRepository."""
        return ExecutionRepository(self._db)

    def get_memory_event_repository(self) -> MemoryEventRepository:
        """Resolves MemoryEventRepository."""
        return MemoryEventRepository(self._db)
