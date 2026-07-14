"""ConversationHistory repository module for Auralis."""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from memory.models.domain_models import ConversationHistoryDomain
from memory.orm.conversation import ConversationHistory
from memory.repository.base_repository import BaseRepository


class ConversationRepository(
    BaseRepository[ConversationHistoryDomain, ConversationHistory]
):
    """Repository mapping ConversationHistory domain models to their database ORM schema."""

    def __init__(self, db: Session) -> None:
        """Initializes the repository with a database session."""
        super().__init__(db, ConversationHistory)

    def _to_domain(self, orm: ConversationHistory) -> ConversationHistoryDomain:
        return ConversationHistoryDomain(
            id=orm.id,
            user_id=orm.user_id,
            session_id=orm.session_id,
            role=orm.role,
            content=orm.content,
            token_count=orm.token_count,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: ConversationHistoryDomain) -> ConversationHistory:
        return ConversationHistory(
            id=domain.id,
            user_id=domain.user_id,
            session_id=domain.session_id,
            role=domain.role,
            content=domain.content,
            token_count=domain.token_count,
            created_at=domain.created_at,
        )
