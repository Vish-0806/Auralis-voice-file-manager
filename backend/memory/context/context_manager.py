"""Context Manager implementation for Auralis."""

import time
import logging
from typing import Any, Dict, Optional

from memory.models.domain_models import ContextDomain
from memory.repository.context_repository import ContextRepository
from memory.context.context_cache import ContextCache
from memory.context.context_validator import ContextValidator
from memory.context.context_expiration import ContextExpiration
from memory.context.context_models import ContextType

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages active execution context state persistence, caching, and TTL lifecycle checks."""

    def __init__(
        self,
        repository: ContextRepository,
        cache: Optional[ContextCache] = None,
        validator: Optional[ContextValidator] = None,
        expiration: Optional[ContextExpiration] = None,
    ) -> None:
        """Initializes ContextManager with dependencies.

        Args:
            repository: Context database repository collaborator.
            cache: Optional custom cache.
            validator: Optional custom validator.
            expiration: Optional custom expiration manager.
        """
        self._repository = repository
        self._cache = cache or ContextCache()
        self._validator = validator or ContextValidator()
        self._expiration = expiration or ContextExpiration()

    def _get_or_create_record(self, user_id: int, session_id: str) -> ContextDomain:
        """Finds or constructs a ContextDomain database entry for a user/session."""
        records = self._repository.search({"user_id": user_id, "session_id": session_id})
        if records:
            return records[0]

        return ContextDomain(
            user_id=user_id,
            session_id=session_id,
            metadata_bag={},
        )

    def save_context(
        self,
        user_id: int,
        session_id: str,
        context_type: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> ContextDomain:
        """Validates, persists, caches, and saves a user context entry.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            context_type: Context type setting.
            value: Setting value payload.
            ttl_seconds: Optional expiration TTL duration.

        Returns:
            The saved ContextDomain object.
        """
        context_type_str = context_type.lower()
        self._validator.validate(context_type_str, value)

        logger.info(
            "Saving session context entry",
            extra={"user_id": user_id, "session_id": session_id, "context_type": context_type_str},
        )
        record = self._get_or_create_record(user_id, session_id)

        # Clear existing expired records first
        bag = self._expiration.clear_expired_context(record.metadata_bag)

        # Calculate expiration
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds
        elif context_type_str == ContextType.TEMPORARY:
            expires_at = time.time() + 60  # Default 60s for temporary context

        # Set new context item
        bag[context_type_str] = {
            "value": value,
            "expires_at": expires_at,
            "updated_at": time.time(),
        }
        record.metadata_bag = bag

        # Set active window or workspace paths in specialized columns if matched
        if context_type_str == ContextType.ACTIVE_WORKSPACE:
            record.workspace_path = value
        elif context_type_str == ContextType.CURRENT_PROJECT:
            record.workspace_path = value

        if record.id is None:
            saved = self._repository.create(record)
        else:
            saved = self._repository.update(record.id, record)

        self._cache.set(user_id, session_id, saved.metadata_bag)
        return saved

    def load_context(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Loads and returns active context values. Automatically purges expired entries.

        Args:
            user_id: User identifier.
            session_id: Session identifier.

        Returns:
            Dictionary mapping context_type keys to their active values.
        """
        # 1. Cache hit check
        cached_bag = self._cache.get(user_id, session_id)
        if cached_bag is not None:
            cleaned = self._expiration.clear_expired_context(cached_bag)
            # If items expired in cache, synchronize cache
            if len(cleaned) != len(cached_bag):
                self._cache.set(user_id, session_id, cleaned)
            return {k: v.get("value") for k, v in cleaned.items()}

        # 2. Database miss lookup
        records = self._repository.search({"user_id": user_id, "session_id": session_id})
        if not records:
            return {}

        record = records[0]
        cleaned_bag = self._expiration.clear_expired_context(record.metadata_bag)

        # If items were purged, persist the updated state to keep database synchronized
        if len(cleaned_bag) != len(record.metadata_bag):
            record.metadata_bag = cleaned_bag
            self._repository.update(record.id, record)

        self._cache.set(user_id, session_id, cleaned_bag)
        return {k: v.get("value") for k, v in cleaned_bag.items()}

    def delete_context(self, user_id: int, session_id: str, context_type: Optional[str] = None) -> bool:
        """Deletes context properties.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            context_type: Optional specific type to delete. If None, deletes the entire record.

        Returns:
            True if deleted, False if not found.
        """
        records = self._repository.search({"user_id": user_id, "session_id": session_id})
        if not records:
            return False

        record = records[0]
        if context_type is None:
            # Delete entire session record
            logger.info("Deleting entire session context record", extra={"user_id": user_id, "session_id": session_id})
            result = self._repository.delete(record.id)
            self._cache.invalidate(user_id, session_id)
            return result

        context_type_str = context_type.lower()
        if context_type_str not in record.metadata_bag:
            return False

        logger.info(
            "Deleting specific session context type",
            extra={"user_id": user_id, "session_id": session_id, "context_type": context_type_str},
        )
        # Remove from bag
        bag = dict(record.metadata_bag)
        bag.pop(context_type_str, None)
        record.metadata_bag = bag

        # Reset columns if matching paths
        if context_type_str in [ContextType.ACTIVE_WORKSPACE, ContextType.CURRENT_PROJECT]:
            record.workspace_path = None

        self._repository.update(record.id, record)
        self._cache.set(user_id, session_id, bag)
        return True

    def restore_context(self, user_id: int, session_id: str, metadata_bag: Dict[str, Any]) -> ContextDomain:
        """Fully overwrites/restores the user session context metadata bag state.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            metadata_bag: Extensible key-value metadata to restore.

        Returns:
            The restored ContextDomain object.
        """
        logger.info(
            "Restoring session context state",
            extra={"user_id": user_id, "session_id": session_id},
        )
        record = self._get_or_create_record(user_id, session_id)

        # Standardize structure for restored metadata bag
        formatted_bag = {}
        for k, v in metadata_bag.items():
            if isinstance(v, dict) and "value" in v:
                formatted_bag[k.lower()] = v
            else:
                formatted_bag[k.lower()] = {
                    "value": v,
                    "expires_at": None,
                    "updated_at": time.time(),
                }

        record.metadata_bag = formatted_bag

        # Extract paths if matching keys
        if "active_workspace" in formatted_bag:
            record.workspace_path = formatted_bag["active_workspace"]["value"]
        elif "current_project" in formatted_bag:
            record.workspace_path = formatted_bag["current_project"]["value"]

        if record.id is None:
            saved = self._repository.create(record)
        else:
            saved = self._repository.update(record.id, record)

        self._cache.set(user_id, session_id, saved.metadata_bag)
        return saved

    def clear_expired_context(self, user_id: int, session_id: str) -> None:
        """Checks and purges all expired context elements for a session.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
        """
        records = self._repository.search({"user_id": user_id, "session_id": session_id})
        if not records:
            return

        record = records[0]
        cleaned_bag = self._expiration.clear_expired_context(record.metadata_bag)

        if len(cleaned_bag) != len(record.metadata_bag):
            record.metadata_bag = cleaned_bag
            self._repository.update(record.id, record)
            self._cache.set(user_id, session_id, cleaned_bag)
            logger.info("Purged expired items from session context", extra={"user_id": user_id, "session_id": session_id})
