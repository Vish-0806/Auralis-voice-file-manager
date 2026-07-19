"""Context repository module for Auralis."""

from typing import Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import ContextDomain
from memory.orm.context import Context
from memory.repository.base_repository import BaseRepository


class ContextRepository(BaseRepository[ContextDomain, Context]):
    """Repository mapping Context domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, Context)

    def _to_domain(self, orm: Context) -> ContextDomain:
        return ContextDomain(
            id=orm.id,
            user_id=orm.user_id,
            session_id=orm.session_id,
            active_window=orm.active_window,
            workspace_path=orm.workspace_path,
            metadata_bag=orm.metadata_bag,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: ContextDomain) -> Context:
        return Context(
            id=domain.id,
            user_id=domain.user_id,
            session_id=domain.session_id,
            active_window=domain.active_window,
            workspace_path=domain.workspace_path,
            metadata_bag=domain.metadata_bag,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get_latest(self, user_id: int) -> Optional[ContextDomain]:
        """Retrieves the most recent context state for a user."""
        results = self.search(filters={"user_id": user_id}, limit=1, order_by=self.orm_model.created_at.desc())
        return results[0] if results else None

    def get_by_session(self, session_id: str) -> Optional[ContextDomain]:
        """Retrieves context state by session identifier."""
        results = self.search(filters={"session_id": session_id}, limit=1)
        return results[0] if results else None
