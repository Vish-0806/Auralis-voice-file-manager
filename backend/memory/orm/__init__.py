"""ORM package initialization.

Imports all declarative database models to register them with the shared
Base.metadata registry, ensuring discovery for future Alembic migrations.
"""

from memory.orm.user import User
from memory.orm.preference import Preference
from memory.orm.workspace import WorkspaceProfile
from memory.orm.context import Context
from memory.orm.conversation import ConversationHistory
from memory.orm.routine import RoutineLearning
from memory.orm.execution import ExecutionHistory
from memory.orm.memory_event import MemoryEvent

__all__ = [
    "User",
    "Preference",
    "WorkspaceProfile",
    "Context",
    "ConversationHistory",
    "RoutineLearning",
    "ExecutionHistory",
    "MemoryEvent",
]
