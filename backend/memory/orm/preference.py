"""SQLAlchemy ORM model defining User preferences."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class Preference(Base):
    """Declarative ORM model representing configuration preferences of a User.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        key: The configuration setting key.
        value: The configuration setting value, stored as JSONB.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_preference_key"),
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="preferences")
