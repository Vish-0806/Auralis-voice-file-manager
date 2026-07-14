"""SQLAlchemy ORM model defining automatically learned Routines."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class RoutineLearning(Base):
    """Declarative ORM model representing learned user routines.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        trigger_event: Event string that triggers this routine.
        action_sequence: Sequence of instructions or automated tasks stored as JSONB.
        confidence_score: Accuracy/confidence value assigned by routine agent.
        is_active: Active routine flag.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "routine_learning"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    trigger_event: Mapped[str] = mapped_column(String(255), nullable=False)
    action_sequence: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="routines")
