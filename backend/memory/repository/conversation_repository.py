"""ConversationHistory repository module for Auralis."""

from typing import List
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

    def get_recent(self, limit: int) -> List[ConversationHistoryDomain]:
        """Retrieves the most recent conversation history items."""
        return self.list_all(limit=limit, order_by=self.orm_model.created_at.desc())

    def get_by_session(self, session_id: str, limit: int) -> List[ConversationHistoryDomain]:
        """Retrieves conversation history items by session identifier."""
        return self.search(filters={"session_id": session_id}, limit=limit, order_by=self.orm_model.created_at.desc())

    def get_by_user(self, user_id: int, limit: int) -> List[ConversationHistoryDomain]:
        """Retrieves conversation history items for a user."""
        return self.search(filters={"user_id": user_id}, limit=limit, order_by=self.orm_model.created_at.desc())
