"""RoutineLearning repository module for Auralis."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import RoutineLearningDomain
from memory.orm.routine import RoutineLearning
from memory.repository.base_repository import BaseRepository


class RoutineRepository(BaseRepository[RoutineLearningDomain, RoutineLearning]):
    """Repository mapping RoutineLearning domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, RoutineLearning)

    def _to_domain(self, orm: RoutineLearning) -> RoutineLearningDomain:
        return RoutineLearningDomain(
            id=orm.id,
            user_id=orm.user_id,
            trigger_event=orm.trigger_event,
            action_sequence=orm.action_sequence,
            confidence_score=orm.confidence_score,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: RoutineLearningDomain) -> RoutineLearning:
        return RoutineLearning(
            id=domain.id,
            user_id=domain.user_id,
            trigger_event=domain.trigger_event,
            action_sequence=domain.action_sequence,
            confidence_score=domain.confidence_score,
            is_active=domain.is_active,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )
