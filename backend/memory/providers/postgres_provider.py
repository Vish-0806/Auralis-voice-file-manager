"""PostgreSQL storage provider for Auralis."""

from contextlib import contextmanager
import logging
from typing import Generator, List, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from memory.database.session import SessionLocal
from memory.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DataIntegrityError,
)
from memory.models.domain_models import (
    MemoryEntry,
    MemoryMetadata,
    MemoryQuery,
    MemoryResult,
    MemoryType,
    UserDomain,
    PreferenceDomain,
    WorkspaceProfileDomain,
    ContextDomain,
    ConversationHistoryDomain,
    RoutineLearningDomain,
    ExecutionHistoryDomain,
    MemoryEventDomain,
)
from memory.providers.base_provider import BaseProvider
from memory.repository.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)


class PostgresProvider(BaseProvider):
    """PostgreSQL storage provider implementation using SQLAlchemy.

    Integrates with the repository layer to persist and retrieve generic
    MemoryEntry structures into specific database tables.
    """

    def __init__(self) -> None:
        """Initializes the PostgreSQL provider."""
        self._default_user_id: Optional[int] = None

    @contextmanager
    def _session_scope(self) -> Generator[Session, None, None]:
        """Context manager for SQLAlchemy database sessions.

        Handles transaction lifecycle commits, rollbacks, and translates
        SQLAlchemy exceptions to domain-specific exceptions.
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except IntegrityError as e:
            logger.error("Database integrity violation occurred during transaction.", exc_info=True)
            session.rollback()
            raise DataIntegrityError(f"Database integrity error: {str(e)}") from e
        except OperationalError as e:
            logger.error("Database connection failure occurred during transaction.", exc_info=True)
            session.rollback()
            raise DatabaseConnectionError(f"Database connection error: {str(e)}") from e
        except SQLAlchemyError as e:
            logger.error("SQLAlchemy database operation failed.", exc_info=True)
            session.rollback()
            raise DatabaseOperationError(f"Database operation error: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error in database transaction.", exc_info=True)
            session.rollback()
            raise e
        finally:
            session.close()

    async def initialize(self) -> None:
        """Initializes database connection and seeds a default user profile."""
        logger.info("Initializing PostgresProvider...")
        try:
            with self._session_scope() as session:
                factory = RepositoryFactory(session)
                user_repo = factory.get_user_repository()

                # Check if default user exists, else create it
                default_user = user_repo.get_by_username("default")
                if not default_user:
                    logger.info("Seeding default user profile in database...")
                    default_user = UserDomain(username="default", email="default@auralis.local")
                    default_user = user_repo.create(default_user)

                self._default_user_id = default_user.id
                logger.info(
                    "PostgresProvider initialization completed successfully",
                    extra={"default_user_id": self._default_user_id},
                )
        except Exception as e:
            logger.critical("Failed to initialize PostgresProvider database session.", exc_info=True)
            raise e

    async def close(self) -> None:
        """Cleans up the provider connection resources (no-op as session pool manages connection lifecycles)."""
        logger.info("Closing PostgresProvider...")

    def _get_user_id(self, entry: MemoryEntry) -> int:
        """Resolves user_id from metadata or returns seeded default user_id."""
        val = entry.metadata.additional_info.get("user_id")
        if val is not None:
            return int(val)
        if self._default_user_id is not None:
            return self._default_user_id
        raise DatabaseOperationError("Provider not initialized: default user_id missing")

    async def save(self, entry: MemoryEntry) -> None:
        """Saves a memory entry to its corresponding specialized repository."""
        logger.info("Saving memory entry to PostgreSQL", extra={"entry_id": entry.id, "type": entry.memory_type})
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            user_id = self._get_user_id(entry)

            if entry.memory_type == MemoryType.PREFERENCE:
                pref_repo = factory.get_preference_repository()
                pref = PreferenceDomain(
                    user_id=user_id,
                    key=entry.id,
                    value={"content": entry.content, "metadata": entry.metadata.model_dump(mode="json")},
                )
                pref_repo.create(pref)

            elif entry.memory_type == MemoryType.SESSION:
                ctx_repo = factory.get_context_repository()
                ctx = ContextDomain(
                    user_id=user_id,
                    session_id=entry.id,
                    workspace_path=entry.content,
                    active_window=entry.metadata.additional_info.get("active_window"),
                    metadata_bag=entry.metadata.model_dump(mode="json"),
                )
                ctx_repo.create(ctx)

            elif entry.memory_type == MemoryType.CONVERSATION:
                conv_repo = factory.get_conversation_repository()
                conv = ConversationHistoryDomain(
                    user_id=user_id,
                    session_id=entry.metadata.additional_info.get("session_id", "default"),
                    role=entry.metadata.additional_info.get("role", "user"),
                    content=entry.content,
                    token_count=entry.metadata.additional_info.get("token_count"),
                )
                conv_repo.create(conv)

            elif entry.memory_type == MemoryType.WORKFLOW:
                routine_repo = factory.get_routine_repository()
                routine = RoutineLearningDomain(
                    user_id=user_id,
                    trigger_event=entry.id,
                    action_sequence={"content": entry.content, "metadata": entry.metadata.model_dump(mode="json")},
                    confidence_score=entry.metadata.additional_info.get("confidence_score", 1.0),
                    is_active=entry.metadata.additional_info.get("is_active", True),
                )
                routine_repo.create(routine)

            elif entry.memory_type == MemoryType.ACTIVITY:
                exec_repo = factory.get_execution_repository()
                exec_hist = ExecutionHistoryDomain(
                    user_id=user_id,
                    action=entry.id,
                    status=entry.metadata.additional_info.get("status", "success"),
                    duration_ms=entry.metadata.additional_info.get("duration_ms"),
                    logs=entry.content,
                    input_parameters=entry.metadata.additional_info.get("input_parameters", {}),
                    output_result=entry.metadata.additional_info.get("output_result", {}),
                )
                exec_repo.create(exec_hist)

            else:
                # Fallback to general MemoryEventRepository
                event_repo = factory.get_memory_event_repository()
                event = MemoryEventDomain(
                    user_id=user_id,
                    event_type=entry.memory_type.value,
                    payload={"id": entry.id, "content": entry.content, "metadata": entry.metadata.model_dump(mode="json")},
                )
                event_repo.create(event)

    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a memory entry by checking repositories based on key lookup."""
        logger.info("Retrieving memory entry from PostgreSQL", extra={"entry_id": entry_id})
        with self._session_scope() as session:
            factory = RepositoryFactory(session)

            # Try retrieving from ContextRepository
            ctx_repo = factory.get_context_repository()
            ctx = ctx_repo.search({"session_id": entry_id})
            if ctx:
                item = ctx[0]
                return MemoryEntry(
                    id=item.session_id,
                    content=item.workspace_path or "",
                    memory_type=MemoryType.SESSION,
                    metadata=MemoryMetadata.model_validate(item.metadata_bag),
                )

            # Try retrieving from PreferenceRepository
            pref_repo = factory.get_preference_repository()
            pref = pref_repo.search({"key": entry_id})
            if pref:
                item = pref[0]
                content = item.value.get("content", "") if isinstance(item.value, dict) else str(item.value)
                meta_dict = item.value.get("metadata", {}) if isinstance(item.value, dict) else {}
                return MemoryEntry(
                    id=item.key,
                    content=content,
                    memory_type=MemoryType.PREFERENCE,
                    metadata=MemoryMetadata.model_validate(meta_dict) if meta_dict else MemoryMetadata(),
                )

            # Try retrieving from RoutineRepository (trigger_event matching entry_id)
            routine_repo = factory.get_routine_repository()
            routine = routine_repo.search({"trigger_event": entry_id})
            if routine:
                item = routine[0]
                content = item.action_sequence.get("content", "") if isinstance(item.action_sequence, dict) else str(item.action_sequence)
                meta_dict = item.action_sequence.get("metadata", {}) if isinstance(item.action_sequence, dict) else {}
                return MemoryEntry(
                    id=item.trigger_event,
                    content=content,
                    memory_type=MemoryType.WORKFLOW,
                    metadata=MemoryMetadata.model_validate(meta_dict) if meta_dict else MemoryMetadata(),
                )

            # Try retrieving from ExecutionRepository (action matching entry_id)
            exec_repo = factory.get_execution_repository()
            execs = exec_repo.search({"action": entry_id})
            if execs:
                item = execs[0]
                return MemoryEntry(
                    id=item.action,
                    content=item.logs or "",
                    memory_type=MemoryType.ACTIVITY,
                    metadata=MemoryMetadata(
                        additional_info={
                            "status": item.status,
                            "duration_ms": item.duration_ms,
                            "input_parameters": item.input_parameters,
                            "output_result": item.output_result,
                        }
                    ),
                )

            # Try fallback memory event repository
            event_repo = factory.get_memory_event_repository()
            events = event_repo.list_all()
            for item in events:
                payload = item.payload
                if isinstance(payload, dict) and payload.get("id") == entry_id:
                    return MemoryEntry(
                        id=entry_id,
                        content=payload.get("content", ""),
                        memory_type=MemoryType(item.event_type),
                        metadata=MemoryMetadata.model_validate(payload.get("metadata", {})),
                    )

            return None

    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Searches memory records across active repositories."""
        logger.info("Searching memory entries in PostgreSQL", extra={"query_text": query.text})
        results: List[MemoryResult] = []
        with self._session_scope() as session:
            factory = RepositoryFactory(session)

            # 1. Search Preferences
            if not query.memory_type or query.memory_type == MemoryType.PREFERENCE:
                pref_repo = factory.get_preference_repository()
                for item in pref_repo.list_all():
                    content = item.value.get("content", "") if isinstance(item.value, dict) else str(item.value)
                    if query.text.lower() in content.lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=item.key,
                                    content=content,
                                    memory_type=MemoryType.PREFERENCE,
                                    metadata=MemoryMetadata.model_validate(item.value.get("metadata", {})) if isinstance(item.value, dict) else MemoryMetadata(),
                                ),
                                score=1.0,
                            )
                        )

            # 2. Search Session contexts
            if not query.memory_type or query.memory_type == MemoryType.SESSION:
                ctx_repo = factory.get_context_repository()
                for item in ctx_repo.list_all():
                    if query.text.lower() in (item.workspace_path or "").lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=item.session_id,
                                    content=item.workspace_path or "",
                                    memory_type=MemoryType.SESSION,
                                    metadata=MemoryMetadata.model_validate(item.metadata_bag),
                                ),
                                score=1.0,
                            )
                        )

            # 3. Search Conversations
            if not query.memory_type or query.memory_type == MemoryType.CONVERSATION:
                conv_repo = factory.get_conversation_repository()
                for item in conv_repo.list_all():
                    if query.text.lower() in item.content.lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=str(item.id),
                                    content=item.content,
                                    memory_type=MemoryType.CONVERSATION,
                                    metadata=MemoryMetadata(
                                        additional_info={
                                            "session_id": item.session_id,
                                            "role": item.role,
                                            "token_count": item.token_count,
                                        }
                                    ),
                                ),
                                score=1.0,
                            )
                        )

            # 4. Search Workflows
            if not query.memory_type or query.memory_type == MemoryType.WORKFLOW:
                routine_repo = factory.get_routine_repository()
                for item in routine_repo.list_all():
                    content = item.action_sequence.get("content", "") if isinstance(item.action_sequence, dict) else str(item.action_sequence)
                    if query.text.lower() in content.lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=item.trigger_event,
                                    content=content,
                                    memory_type=MemoryType.WORKFLOW,
                                    metadata=MemoryMetadata.model_validate(item.action_sequence.get("metadata", {})) if isinstance(item.action_sequence, dict) else MemoryMetadata(),
                                ),
                                score=1.0,
                            )
                        )

            # 5. Search Execution Histories
            if not query.memory_type or query.memory_type == MemoryType.ACTIVITY:
                exec_repo = factory.get_execution_repository()
                for item in exec_repo.list_all():
                    if query.text.lower() in (item.logs or "").lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=item.action,
                                    content=item.logs or "",
                                    memory_type=MemoryType.ACTIVITY,
                                    metadata=MemoryMetadata(
                                        additional_info={
                                            "status": item.status,
                                            "duration_ms": item.duration_ms,
                                            "input_parameters": item.input_parameters,
                                            "output_result": item.output_result,
                                        }
                                    ),
                                ),
                                score=1.0,
                            )
                        )

            # 6. Fallback/Events Search
            event_repo = factory.get_memory_event_repository()
            for item in event_repo.list_all():
                if query.memory_type and query.memory_type.value != item.event_type:
                    continue
                payload = item.payload
                if isinstance(payload, dict):
                    content = payload.get("content", "")
                    if query.text.lower() in content.lower():
                        results.append(
                            MemoryResult(
                                entry=MemoryEntry(
                                    id=payload.get("id", str(item.id)),
                                    content=content,
                                    memory_type=MemoryType(item.event_type),
                                    metadata=MemoryMetadata.model_validate(payload.get("metadata", {})),
                                ),
                                score=1.0,
                            )
                        )

        return results[:query.limit]

    async def update(self, entry_id: str, entry: MemoryEntry) -> None:
        """Updates a memory entry in PostgreSQL.

        Raises:
            KeyError: If the entry is not found.
        """
        logger.info("Updating memory entry in PostgreSQL", extra={"entry_id": entry_id, "type": entry.memory_type})
        with self._session_scope() as session:
            factory = RepositoryFactory(session)

            if entry.memory_type == MemoryType.PREFERENCE:
                pref_repo = factory.get_preference_repository()
                pref = pref_repo.search({"key": entry_id})
                if not pref:
                    raise KeyError(f"Preference memory with key {entry_id} not found.")
                pref_item = pref[0]
                pref_item.value = {"content": entry.content, "metadata": entry.metadata.model_dump(mode="json")}
                pref_repo.update(pref_item.id, pref_item)

            elif entry.memory_type == MemoryType.SESSION:
                ctx_repo = factory.get_context_repository()
                ctx = ctx_repo.search({"session_id": entry_id})
                if not ctx:
                    raise KeyError(f"Session context memory with session_id {entry_id} not found.")
                ctx_item = ctx[0]
                ctx_item.workspace_path = entry.content
                ctx_item.active_window = entry.metadata.additional_info.get("active_window")
                ctx_item.metadata_bag = entry.metadata.model_dump(mode="json")
                ctx_repo.update(ctx_item.id, ctx_item)

            elif entry.memory_type == MemoryType.CONVERSATION:
                conv_repo = factory.get_conversation_repository()
                conv = conv_repo.get_by_id(int(entry_id)) if entry_id.isdigit() else None
                if not conv:
                    raise KeyError(f"Conversation memory with ID {entry_id} not found.")
                conv.content = entry.content
                conv.role = entry.metadata.additional_info.get("role", conv.role)
                conv.token_count = entry.metadata.additional_info.get("token_count", conv.token_count)
                conv_repo.update(conv.id, conv)

            elif entry.memory_type == MemoryType.WORKFLOW:
                routine_repo = factory.get_routine_repository()
                routine = routine_repo.search({"trigger_event": entry_id})
                if not routine:
                    raise KeyError(f"Workflow memory with trigger_event {entry_id} not found.")
                routine_item = routine[0]
                routine_item.action_sequence = {"content": entry.content, "metadata": entry.metadata.model_dump(mode="json")}
                routine_repo.update(routine_item.id, routine_item)

            elif entry.memory_type == MemoryType.ACTIVITY:
                exec_repo = factory.get_execution_repository()
                execs = exec_repo.search({"action": entry_id})
                if not execs:
                    raise KeyError(f"Execution memory with action {entry_id} not found.")
                exec_item = execs[0]
                exec_item.logs = entry.content
                exec_item.status = entry.metadata.additional_info.get("status", exec_item.status)
                exec_repo.update(exec_item.id, exec_item)

            else:
                # Update general event
                event_repo = factory.get_memory_event_repository()
                events = event_repo.list_all()
                found = False
                for item in events:
                    if isinstance(item.payload, dict) and item.payload.get("id") == entry_id:
                        item.payload = {"id": entry_id, "content": entry.content, "metadata": entry.metadata.model_dump(mode="json")}
                        event_repo.update(item.id, item)
                        found = True
                        break
                if not found:
                    raise KeyError(f"Fallback event memory with ID {entry_id} not found.")

    async def delete(self, entry_id: str) -> None:
        """Deletes a memory entry from PostgreSQL."""
        logger.info("Deleting memory entry from PostgreSQL", extra={"entry_id": entry_id})
        with self._session_scope() as session:
            factory = RepositoryFactory(session)

            # Try context
            ctx_repo = factory.get_context_repository()
            for item in ctx_repo.search({"session_id": entry_id}):
                ctx_repo.delete(item.id)

            # Try preferences
            pref_repo = factory.get_preference_repository()
            for item in pref_repo.search({"key": entry_id}):
                pref_repo.delete(item.id)

            # Try conversation
            conv_repo = factory.get_conversation_repository()
            if entry_id.isdigit():
                conv_repo.delete(int(entry_id))

            # Try workflows
            routine_repo = factory.get_routine_repository()
            for item in routine_repo.search({"trigger_event": entry_id}):
                routine_repo.delete(item.id)

            # Try activity
            exec_repo = factory.get_execution_repository()
            for item in exec_repo.search({"action": entry_id}):
                exec_repo.delete(item.id)

            # Try event log fallback
            event_repo = factory.get_memory_event_repository()
            for item in event_repo.list_all():
                if isinstance(item.payload, dict) and item.payload.get("id") == entry_id:
                    event_repo.delete(item.id)

    async def list_entries(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Lists memory entries from database."""
        logger.info("Listing memory entries from PostgreSQL", extra={"memory_type": memory_type})
        entries: List[MemoryEntry] = []
        with self._session_scope() as session:
            factory = RepositoryFactory(session)

            if not memory_type or memory_type == MemoryType.PREFERENCE.value:
                pref_repo = factory.get_preference_repository()
                for item in pref_repo.list_all():
                    content = item.value.get("content", "") if isinstance(item.value, dict) else str(item.value)
                    entries.append(
                        MemoryEntry(
                            id=item.key,
                            content=content,
                            memory_type=MemoryType.PREFERENCE,
                            metadata=MemoryMetadata.model_validate(item.value.get("metadata", {})) if isinstance(item.value, dict) else MemoryMetadata(),
                        )
                    )

            if not memory_type or memory_type == MemoryType.SESSION.value:
                ctx_repo = factory.get_context_repository()
                for item in ctx_repo.list_all():
                    entries.append(
                        MemoryEntry(
                            id=item.session_id,
                            content=item.workspace_path or "",
                            memory_type=MemoryType.SESSION,
                            metadata=MemoryMetadata.model_validate(item.metadata_bag),
                        )
                    )

            if not memory_type or memory_type == MemoryType.CONVERSATION.value:
                conv_repo = factory.get_conversation_repository()
                for item in conv_repo.list_all():
                    entries.append(
                        MemoryEntry(
                            id=str(item.id),
                            content=item.content,
                            memory_type=MemoryType.CONVERSATION,
                            metadata=MemoryMetadata(
                                additional_info={
                                    "session_id": item.session_id,
                                    "role": item.role,
                                    "token_count": item.token_count,
                                }
                            ),
                        )
                    )

            if not memory_type or memory_type == MemoryType.WORKFLOW.value:
                routine_repo = factory.get_routine_repository()
                for item in routine_repo.list_all():
                    content = item.action_sequence.get("content", "") if isinstance(item.action_sequence, dict) else str(item.action_sequence)
                    entries.append(
                        MemoryEntry(
                            id=item.trigger_event,
                            content=content,
                            memory_type=MemoryType.WORKFLOW,
                            metadata=MemoryMetadata.model_validate(item.action_sequence.get("metadata", {})) if isinstance(item.action_sequence, dict) else MemoryMetadata(),
                        )
                    )

            if not memory_type or memory_type == MemoryType.ACTIVITY.value:
                exec_repo = factory.get_execution_repository()
                for item in exec_repo.list_all():
                    entries.append(
                        MemoryEntry(
                            id=item.action,
                            content=item.logs or "",
                            memory_type=MemoryType.ACTIVITY,
                            metadata=MemoryMetadata(
                                additional_info={
                                    "status": item.status,
                                    "duration_ms": item.duration_ms,
                                    "input_parameters": item.input_parameters,
                                    "output_result": item.output_result,
                                }
                            ),
                        )
                    )

            # Fallback event logs
            event_repo = factory.get_memory_event_repository()
            for item in event_repo.list_all():
                if memory_type and memory_type != item.event_type:
                    continue
                payload = item.payload
                if isinstance(payload, dict):
                    entries.append(
                        MemoryEntry(
                            id=payload.get("id", str(item.id)),
                            content=payload.get("content", ""),
                            memory_type=MemoryType(item.event_type),
                            metadata=MemoryMetadata.model_validate(payload.get("metadata", {})),
                        )
                    )

        return entries

    async def get_recent_conversations(self, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_conversation_repository()
            items = repo.get_recent(limit)
            return [
                MemoryEntry(
                    id=str(item.id),
                    content=item.content,
                    memory_type=MemoryType.CONVERSATION,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "session_id": item.session_id,
                            "role": item.role,
                            "token_count": item.token_count,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_conversations_by_session(self, session_id: str, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_conversation_repository()
            items = repo.get_by_session(session_id, limit)
            return [
                MemoryEntry(
                    id=str(item.id),
                    content=item.content,
                    memory_type=MemoryType.CONVERSATION,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "session_id": item.session_id,
                            "role": item.role,
                            "token_count": item.token_count,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_conversations_by_user(self, user_id: int, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_conversation_repository()
            items = repo.get_by_user(user_id, limit)
            return [
                MemoryEntry(
                    id=str(item.id),
                    content=item.content,
                    memory_type=MemoryType.CONVERSATION,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "session_id": item.session_id,
                            "role": item.role,
                            "token_count": item.token_count,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_recent_executions(self, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_execution_repository()
            items = repo.get_recent(limit)
            return [
                MemoryEntry(
                    id=item.action,
                    content=item.logs or "",
                    memory_type=MemoryType.ACTIVITY,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "status": item.status,
                            "duration_ms": item.duration_ms,
                            "input_parameters": item.input_parameters,
                            "output_result": item.output_result,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_failed_executions(self, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_execution_repository()
            items = repo.get_failed(limit)
            return [
                MemoryEntry(
                    id=item.action,
                    content=item.logs or "",
                    memory_type=MemoryType.ACTIVITY,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "status": item.status,
                            "duration_ms": item.duration_ms,
                            "input_parameters": item.input_parameters,
                            "output_result": item.output_result,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_successful_executions(self, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_execution_repository()
            items = repo.get_successful(limit)
            return [
                MemoryEntry(
                    id=item.action,
                    content=item.logs or "",
                    memory_type=MemoryType.ACTIVITY,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            "status": item.status,
                            "duration_ms": item.duration_ms,
                            "input_parameters": item.input_parameters,
                            "output_result": item.output_result,
                            "user_id": item.user_id,
                        }
                    )
                ) for item in items
            ]

    async def get_latest_context(self, user_id: int) -> Optional[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_context_repository()
            item = repo.get_latest(user_id)
            if not item:
                return None
            info = dict(item.metadata_bag) if item.metadata_bag else {}
            info["user_id"] = item.user_id
            info["session_id"] = item.session_id
            return MemoryEntry(
                id=item.session_id,
                content=item.workspace_path or "",
                memory_type=MemoryType.SESSION,
                metadata=MemoryMetadata(
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    additional_info=info
                )
            )

    async def get_context_by_session(self, session_id: str) -> Optional[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_context_repository()
            item = repo.get_by_session(session_id)
            if not item:
                return None
            info = dict(item.metadata_bag) if item.metadata_bag else {}
            info["user_id"] = item.user_id
            info["session_id"] = item.session_id
            return MemoryEntry(
                id=item.session_id,
                content=item.workspace_path or "",
                memory_type=MemoryType.SESSION,
                metadata=MemoryMetadata(
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    additional_info=info
                )
            )

    async def get_preference_by_key(self, user_id: int, key: str) -> Optional[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_preference_repository()
            item = repo.get_by_key(user_id, key)
            if not item:
                return None
            content = item.value.get("content", "") if isinstance(item.value, dict) else str(item.value)
            metadata = MemoryMetadata.model_validate(item.value.get("metadata", {})) if isinstance(item.value, dict) else MemoryMetadata()
            metadata.created_at = item.created_at
            metadata.additional_info["user_id"] = item.user_id
            return MemoryEntry(
                id=item.key,
                content=content,
                memory_type=MemoryType.PREFERENCE,
                metadata=metadata
            )

    async def get_recent_events(self, limit: int) -> List[MemoryEntry]:
        with self._session_scope() as session:
            factory = RepositoryFactory(session)
            repo = factory.get_memory_event_repository()
            items = repo.get_recent(limit)
            return [
                MemoryEntry(
                    id=item.payload.get("id", str(item.id)) if isinstance(item.payload, dict) else str(item.id),
                    content=item.payload.get("content", "") if isinstance(item.payload, dict) else "",
                    memory_type=MemoryType(item.event_type) if hasattr(MemoryType, item.event_type.upper()) else MemoryType.LONG_TERM,
                    metadata=MemoryMetadata(
                        created_at=item.created_at,
                        additional_info={
                            **(item.payload.get("metadata", {}) if isinstance(item.payload, dict) else {}),
                            "user_id": item.user_id
                        }
                    )
                ) for item in items
            ]
