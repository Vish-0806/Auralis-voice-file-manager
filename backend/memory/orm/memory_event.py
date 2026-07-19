"""SQLAlchemy ORM model defining Memory state change Events."""

from __future__ import annotations

from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import String, DateTime, ForeignKey, func
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class MemoryEvent(Base):
    """Declarative ORM model representing memory state changes.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        event_type: Type descriptor of the event.
        payload: Event body stored as JSONB.
        created_at: Event creation timestamp.
    """

    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="memory_events")
