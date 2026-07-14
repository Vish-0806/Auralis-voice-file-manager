"""SQLAlchemy ORM model defining Conversation History memory."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class ConversationHistory(Base):
    """Declarative ORM model representing conversational turns.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        session_id: The session string representing the conversation thread.
        role: The conversational role (e.g. "user", "assistant", "system").
        content: The text payload of the turn.
        token_count: Optional tracked tokens in the content.
        created_at: Creation timestamp.
    """

    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="conversations")
