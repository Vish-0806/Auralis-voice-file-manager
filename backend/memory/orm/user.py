"""SQLAlchemy ORM model defining the User entity."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import String, DateTime, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from memory.database import Base


class User(Base):
    """Declarative ORM model representing a User in Auralis.

    Attributes:
        id: Primary key identifier.
        username: Unique username for the user.
        email: Optional unique email address.
        created_at: Date and time of user creation.
        updated_at: Date and time of last profile modification.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
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
    preferences: Mapped[List[Preference]] = relationship(
        "Preference", back_populates="user", cascade="all, delete-orphan"
    )
    workspace_profiles: Mapped[List[WorkspaceProfile]] = relationship(
        "WorkspaceProfile", back_populates="user", cascade="all, delete-orphan"
    )
    contexts: Mapped[List[Context]] = relationship(
        "Context", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[List[ConversationHistory]] = relationship(
        "ConversationHistory", back_populates="user", cascade="all, delete-orphan"
    )
    routines: Mapped[List[RoutineLearning]] = relationship(
        "RoutineLearning", back_populates="user", cascade="all, delete-orphan"
    )
    executions: Mapped[List[ExecutionHistory]] = relationship(
        "ExecutionHistory", back_populates="user", cascade="all, delete-orphan"
    )
    memory_events: Mapped[List[MemoryEvent]] = relationship(
        "MemoryEvent", back_populates="user", cascade="all, delete-orphan"
    )
