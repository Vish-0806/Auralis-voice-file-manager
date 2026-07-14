"""Context repository module for Auralis."""

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
