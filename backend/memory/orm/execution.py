"""SQLAlchemy ORM model defining action Execution History."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import String, DateTime, ForeignKey, func
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class ExecutionHistory(Base):
    """Declarative ORM model representing automation action logs.

    Attributes:
        id: Primary key identifier.
        user_id: ForeignKey referencing users.id.
        action: Identifier of the automated capability/action executed.
        status: Outcome status of the execution (e.g. "success", "failed").
        duration_ms: Total run time in milliseconds.
        logs: Standard error or execution text output.
        input_parameters: Dict of parameters supplied during call, stored as JSONB.
        output_result: Dict of output returned by action, stored as JSONB.
        created_at: Execution timestamp.
    """

    __tablename__ = "execution_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    input_parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="executions")
