"""User Context Service public interface module."""

import logging
from typing import Any, Dict, Optional

from memory.models.domain_models import ContextDomain
from memory.context.context_manager import ContextManager

logger = logging.getLogger(__name__)


class ContextService:
    """Sole public gateway/API for all Context Memory operations in Auralis."""

    def __init__(self, manager: Optional[ContextManager] = None) -> None:
        """Initializes the ContextService.

        If no manager is provided, dynamically resolves dependency using SessionLocal
        and the ContextRepository.

        Args:
            manager: Optional custom ContextManager instance.
        """
        if manager is not None:
            self._manager = manager
        else:
            from memory.database.session import SessionLocal
            from memory.repository.context_repository import ContextRepository

            self._db = SessionLocal()
            repository = ContextRepository(self._db)
            self._manager = ContextManager(repository)

    def __del__(self) -> None:
        """Ensures the internal database session is closed correctly when garbage collected."""
        if hasattr(self, "_db"):
            try:
                self._db.close()
            except Exception:
                pass

    def save(
        self,
        user_id: int,
        session_id: str,
        context_type: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> ContextDomain:
        """Validates and persists a context setting value.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            context_type: Context type identifier.
            value: Value state to save.
            ttl_seconds: Optional expiry duration in seconds.

        Returns:
            The saved ContextDomain object.
        """
        return self._manager.save_context(user_id, session_id, context_type, value, ttl_seconds)

    def load(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Loads and returns all active context values for a session.

        Args:
            user_id: User identifier.
            session_id: Session identifier.

        Returns:
            Dictionary mapping active context types to values.
        """
        return self._manager.load_context(user_id, session_id)

    def update(
        self,
        user_id: int,
        session_id: str,
        context_type: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> ContextDomain:
        """Updates an active context value (equivalent to save).

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            context_type: Context type identifier.
            value: Updated value state to save.
            ttl_seconds: Optional updated expiry duration.

        Returns:
            The updated ContextDomain object.
        """
        return self._manager.save_context(user_id, session_id, context_type, value, ttl_seconds)

    def delete(self, user_id: int, session_id: str, context_type: Optional[str] = None) -> bool:
        """Deletes a session context record or a specific context type value.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            context_type: Optional specific type to delete. If None, purges entire record.

        Returns:
            True if deleted, False if not found.
        """
        return self._manager.delete_context(user_id, session_id, context_type)

    def restore(self, user_id: int, session_id: str, metadata_bag: Dict[str, Any]) -> ContextDomain:
        """Fully restores/overwrites a session context state.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            metadata_bag: Full context map state to restore.

        Returns:
            The restored ContextDomain object.
        """
        return self._manager.restore_context(user_id, session_id, metadata_bag)

    def clear_expired(self, user_id: int, session_id: str) -> None:
        """Checks and purges all expired context entries for a session.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
        """
        self._manager.clear_expired_context(user_id, session_id)
