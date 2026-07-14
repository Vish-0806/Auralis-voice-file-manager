"""SQLAlchemy ORM model defining User workspace profiles."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class WorkspaceProfile(Base):
    """Declarative ORM model representing user workspace paths and setups.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        name: Name of the workspace profile.
        path: Root directory path.
        settings: Profile settings bag stored as JSONB.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "workspace_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
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
    user: Mapped[User] = relationship("User", back_populates="workspace_profiles")
