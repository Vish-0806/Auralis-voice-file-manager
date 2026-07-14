"""SQLAlchemy ORM model defining the active execution Context."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class Context(Base):
    """Declarative ORM model representing active execution states/parameters.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        session_id: Active session identifier.
        active_window: Name or descriptor of the currently focused OS window.
        workspace_path: The active directory workspace path.
        metadata_bag: Extensible key-value metadata stored as JSONB.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    active_window: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workspace_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    metadata_bag: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
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
    user: Mapped[User] = relationship("User", back_populates="contexts")
