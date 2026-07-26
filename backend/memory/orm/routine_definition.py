"""SQLAlchemy ORM model defining automatically learned/created Routines."""

from __future__ import annotations

from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import String, DateTime, ForeignKey, func
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class RoutineDefinition(Base):
    """Declarative ORM model representing autonomous routine definitions.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        name: Name of the routine.
        description: Rationale/description of the routine context.
        steps: Sequential list of actions stored as JSONB.
        trigger_condition: Trigger rules stored as JSONB.
        is_active: Active routine flag.
        version: Routine model schema/parameters version integer.
        metadata_info: Metric logs, execution statistics, tags, categories, version history stored as JSONB.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "routine_definition"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    steps: Mapped[dict] = mapped_column(JSONB, nullable=False)
    trigger_condition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    metadata_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to user
    user = relationship("User")
