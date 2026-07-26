"""Memory coordinator module.

Defines the MemoryManager which coordinates and orchestrates operations
across memory tiers, delegating direct persistence actions to repositories
and returning domain models to the service layer.
"""

import logging
from typing import Any, List, Optional
from memory.models.domain_models import MemoryEntry, MemoryQuery, MemoryResult
from memory.repository.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)


class MemoryManager:
    """Coordinating manager for memory operations.

    Orchestrates business logic for memory retrieval, injection, and updates,
    delegating the low-level data storage operations to repositories.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        """Initializes the MemoryManager.

        Args:
            repository: The MemoryRepository instance.
        """
        self._repository = repository
        logger.debug(
            "MemoryManager initialized with repository",
            extra={"repository_class": repository.__class__.__name__},
        )

    async def save_memory(self, entry: MemoryEntry) -> MemoryEntry:
        """Coordinates saving a memory entry.

        Args:
            entry: The MemoryEntry domain model to save.

        Returns:
            The saved MemoryEntry domain model.
        """
        logger.info(
            "MemoryManager coordinating save",
            extra={"entry_id": entry.id, "memory_type": entry.memory_type.value},
        )
        await self._repository.add(entry)
        return entry

    async def get_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Coordinates retrieving a memory entry by ID.

        Args:
            entry_id: Unique string identifier of the memory entry.

        Returns:
            The retrieved MemoryEntry domain model if found, else None.
        """
        logger.info(
            "MemoryManager coordinating get",
            extra={"entry_id": entry_id},
        )
        return await self._repository.get_by_id(entry_id)

    async def search_memories(self, query: MemoryQuery) -> List[MemoryResult]:
        """Coordinates searching memories.

        Args:
            query: The MemoryQuery domain model parameters.

        Returns:
            A list of matching MemoryResult domain models.
        """
        logger.info(
            "MemoryManager coordinating search",
            extra={"query_text": query.text, "limit": query.limit},
        )
        return await self._repository.search(query)

    async def update_memory(self, entry_id: str, entry: MemoryEntry) -> MemoryEntry:
        """Coordinates updating an existing memory entry.

        Args:
            entry_id: Unique string identifier of the memory entry to update.
            entry: The updated MemoryEntry domain model.

        Returns:
            The updated MemoryEntry domain model.
        """
        logger.info(
            "MemoryManager coordinating update",
            extra={"entry_id": entry_id},
        )
        await self._repository.update(entry_id, entry)
        return entry

    async def delete_memory(self, entry_id: str) -> None:
        """Coordinates deleting a memory entry by ID.

        Args:
            entry_id: Unique string identifier of the memory entry.
        """
        logger.info(
            "MemoryManager coordinating delete",
            extra={"entry_id": entry_id},
        )
        await self._repository.delete(entry_id)

    async def list_memories(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Coordinates listing all memory entries, optionally filtered by type.

        Args:
            memory_type: Optional memory type string to filter results.

        Returns:
            A list of matching MemoryEntry domain models.
        """
        logger.info(
            "MemoryManager coordinating list",
            extra={"memory_type": memory_type},
        )
        return await self._repository.list_all(memory_type)

    async def get_recent_conversations(self, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_recent_conversations(limit)

    async def get_conversations_by_session(self, session_id: str, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_conversations_by_session(session_id, limit)

    async def get_conversations_by_user(self, user_id: int, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_conversations_by_user(user_id, limit)

    async def get_recent_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_recent_executions(limit)

    async def get_failed_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_failed_executions(limit)

    async def get_successful_executions(self, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_successful_executions(limit)

    async def get_latest_context(self, user_id: int) -> Optional[MemoryEntry]:
        return await self._repository.get_latest_context(user_id)

    async def get_context_by_session(self, session_id: str) -> Optional[MemoryEntry]:
        return await self._repository.get_context_by_session(session_id)

    async def get_preference_by_key(self, user_id: int, key: str) -> Optional[MemoryEntry]:
        return await self._repository.get_preference_by_key(user_id, key)

    async def get_recent_events(self, limit: int) -> List[MemoryEntry]:
        return await self._repository.get_recent_events(limit)

    async def get_workspace_context(self, user_id: int, path: str) -> Optional[MemoryEntry]:
        return await self._repository.get_workspace_context(user_id, path)

    async def get_user_preferences(self, user_id: int) -> List[MemoryEntry]:
        return await self._repository.get_user_preferences(user_id)

    async def get_resolved_preferences(self, user_id: int) -> dict:
        """Returns a dictionary mapping preference categories to resolved values."""
        entries = await self.get_user_preferences(user_id)
        resolved = {}
        for entry in entries:
            val = entry.metadata.additional_info.get("value") if entry.metadata.additional_info else None
            resolved[entry.id] = val if val is not None else entry.content
        return resolved

    async def save_resolved_preference(self, resolved_pref: Any) -> None:
        """Saves a resolved preference as a MemoryEntry."""
        from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryType
        from datetime import datetime, timezone
        entry = MemoryEntry(
            id=resolved_pref.category,
            content=str(resolved_pref.value),
            memory_type=MemoryType.PREFERENCE,
            metadata=MemoryMetadata(
                created_at=resolved_pref.resolved_at,
                updated_at=datetime.now(timezone.utc),
                additional_info={
                    "user_id": resolved_pref.user_id,
                    "value": resolved_pref.value,
                    "confidence_score": resolved_pref.confidence_score,
                    "source": resolved_pref.source,
                    "metadata": resolved_pref.metadata,
                }
            )
        )
        await self.save_memory(entry)

    async def get_preference_observations(self, user_id: int, limit: int = 100) -> list:
        """Retrieves parsed preference observations from execution history."""
        successful_entries = await self.get_successful_executions(limit)
        observations = []
        from memory.preferences.preference_learning import PreferenceObservation
        for entry in successful_entries:
            info = entry.metadata.additional_info or {}
            entry_user_id = info.get("user_id")
            if entry_user_id is not None and str(entry_user_id) != str(user_id):
                continue
            obs = self._parse_observation_from_entry(user_id, entry)
            if obs:
                observations.append(obs)
        return observations

    def _parse_observation_from_entry(self, user_id: int, entry: MemoryEntry) -> Optional[Any]:
        from memory.preferences.preference_learning import PreferenceObservation
        info = entry.metadata.additional_info or {}
        obs_data = info.get("preference_observation")
        if isinstance(obs_data, dict):
            try:
                return PreferenceObservation(
                    user_id=user_id,
                    category=obs_data.get("category"),
                    value=obs_data.get("value"),
                    timestamp=entry.metadata.created_at,
                    is_override=obs_data.get("is_override", False),
                    execution_id=entry.id.replace("_activity", ""),
                    execution_status=info.get("status", "SUCCESS"),
                    context_metadata=info.get("input_parameters", {})
                )
            except Exception:
                pass

        action = str(entry.id).lower()
        params = info.get("input_parameters") or {}
        params_str = str(params).lower()
        status = info.get("status", "SUCCESS")

        category = None
        value = None

        if any(x in action or x in params_str for x in ["shell", "terminal", "powershell", "pwsh", "bash", "zsh", "cmd"]):
            category = "Shell"
            if "powershell" in params_str or "powershell" in action or "pwsh" in params_str or "pwsh" in action:
                value = "PowerShell"
            elif "bash" in params_str or "bash" in action:
                value = "Bash"
            elif "zsh" in params_str or "zsh" in action:
                value = "Zsh"
            elif "cmd" in params_str or "cmd" in action:
                value = "CMD"
        elif any(x in action or x in params_str for x in ["browser", "chrome", "firefox", "safari", "edge"]):
            category = "Browser"
            if "chrome" in params_str or "chrome" in action:
                value = "Chrome"
            elif "firefox" in params_str or "firefox" in action:
                value = "Firefox"
            elif "safari" in params_str or "safari" in action:
                value = "Safari"
            elif "edge" in params_str or "edge" in action:
                value = "Edge"
        elif any(x in action or x in params_str for x in ["ide", "editor", "vscode", "vs code", "pycharm", "sublime"]):
            category = "IDE"
            if "vscode" in params_str or "vs code" in params_str or "vscode" in action or "vs code" in action:
                value = "VS Code"
            elif "pycharm" in params_str or "pycharm" in action:
                value = "PyCharm"
            elif "sublime" in params_str or "sublime" in action:
                value = "Sublime Text"

        if category and value:
            return PreferenceObservation(
                user_id=user_id,
                category=category,
                value=value,
                timestamp=entry.metadata.created_at,
                is_override=False,
                execution_id=entry.id.replace("_activity", ""),
                execution_status=status,
                context_metadata=params
            )
        return None

    async def save_workflow_observation(self, observation: Any) -> None:
        """Saves a workflow observation to the repository."""
        from memory.workflows import ObservationRepository
        provider = getattr(self._repository, "_provider", None)
        if provider:
            repo = ObservationRepository(provider)
            await repo.save(observation)

    async def get_workflow_observations(self, user_id: int) -> list:
        """Retrieves all workflow observations for a user."""
        from memory.workflows import ObservationRepository
        provider = getattr(self._repository, "_provider", None)
        if provider:
            repo = ObservationRepository(provider)
            return await repo.list_by_user(user_id)
        return []

    async def get_workflow_sequences(self, user_id: int) -> list:
        """Retrieves all distinct workflow sequences observed for a user."""
        observations = await self.get_workflow_observations(user_id)
        unique_sequences = {}
        for obs in observations:
            seq = obs.sequence
            if seq.sequence_hash not in unique_sequences:
                unique_sequences[seq.sequence_hash] = seq
        return list(unique_sequences.values())
