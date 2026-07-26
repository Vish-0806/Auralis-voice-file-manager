"""SQLAlchemy ORM model defining Proactive Recommendations."""

from __future__ import annotations

from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import String, DateTime, ForeignKey, func, Float
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class ProactiveRecommendation(Base):
    """Declarative ORM model representing proactive assistant suggestions.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        suggestion_text: User-facing descriptive message.
        action_type: Intended execution capability command name.
        confidence_score: Accuracy/confidence value.
        scoring_details: Breakdown parameters (frequency, recency, workspace, etc) stored as JSONB.
        status: Recommendation lifecycle status ('pending', 'accepted', 'dismissed', 'ignored').
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "proactive_recommendation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    suggestion_text: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    scoring_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
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
    user = relationship("User")
