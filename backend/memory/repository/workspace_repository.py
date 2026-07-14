"""Workspace profile repository module for Auralis."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import WorkspaceProfileDomain
from memory.orm.workspace import WorkspaceProfile
from memory.repository.base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[WorkspaceProfileDomain, WorkspaceProfile]):
    """Repository mapping WorkspaceProfile domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, WorkspaceProfile)

    def _to_domain(self, orm: WorkspaceProfile) -> WorkspaceProfileDomain:
        return WorkspaceProfileDomain(
            id=orm.id,
            user_id=orm.user_id,
            name=orm.name,
            path=orm.path,
            settings=orm.settings,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: WorkspaceProfileDomain) -> WorkspaceProfile:
        return WorkspaceProfile(
            id=domain.id,
            user_id=domain.user_id,
            name=domain.name,
            path=domain.path,
            settings=domain.settings,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )
