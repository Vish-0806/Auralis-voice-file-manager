"""RoutineDefinition repository mapping for SQL databases."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.repository.base_repository import BaseRepository
from memory.orm.routine_definition import RoutineDefinition
from memory.routines.models import RoutineDefinitionDomain


class RoutineDefinitionRepository(BaseRepository[RoutineDefinitionDomain, RoutineDefinition]):
    """Repository mapping RoutineDefinition domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, RoutineDefinition)

    def _to_domain(self, orm: RoutineDefinition) -> RoutineDefinitionDomain:
        return RoutineDefinitionDomain(
            id=orm.id,
            user_id=orm.user_id,
            name=orm.name,
            description=orm.description,
            steps=orm.steps.get("steps", []) if isinstance(orm.steps, dict) else orm.steps,
            trigger_condition=orm.trigger_condition,
            is_active=orm.is_active,
            version=orm.version,
            metadata_info=orm.metadata_info,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: RoutineDefinitionDomain) -> RoutineDefinition:
        return RoutineDefinition(
            id=domain.id,
            user_id=domain.user_id,
            name=domain.name,
            description=domain.description,
            steps={"steps": domain.steps} if isinstance(domain.steps, list) else domain.steps,
            trigger_condition=domain.trigger_condition,
            is_active=domain.is_active,
            version=domain.version,
            metadata_info=domain.metadata_info,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )
