"""MemoryEvent repository module for Auralis."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import MemoryEventDomain
from memory.orm.memory_event import MemoryEvent
from memory.repository.base_repository import BaseRepository


class MemoryEventRepository(BaseRepository[MemoryEventDomain, MemoryEvent]):
    """Repository mapping MemoryEvent domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, MemoryEvent)

    def _to_domain(self, orm: MemoryEvent) -> MemoryEventDomain:
        return MemoryEventDomain(
            id=orm.id,
            user_id=orm.user_id,
            event_type=orm.event_type,
            payload=orm.payload,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: MemoryEventDomain) -> MemoryEvent:
        return MemoryEvent(
            id=domain.id,
            user_id=domain.user_id,
            event_type=domain.event_type,
            payload=domain.payload,
            created_at=domain.created_at,
        )
