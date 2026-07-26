"""Repository for persisted WorkflowObservation models utilizing a storage provider."""

import logging
from datetime import datetime
from typing import Any, List, Optional

from memory.models.domain_models import MemoryEntry, MemoryMetadata, MemoryType, MemoryQuery
from memory.providers.base_provider import BaseProvider
from memory.workflows.workflow_models import WorkflowObservation, WorkflowSequence, ensure_utc

logger = logging.getLogger(__name__)


class ObservationRepository:
    """Repository class for persisting and querying WorkflowObservation models using a BaseProvider."""

    def __init__(self, provider: BaseProvider) -> None:
        """Initializes the repository with a storage provider."""
        self._provider = provider

    def _to_memory_entry(self, obs: WorkflowObservation) -> MemoryEntry:
        """Converts a WorkflowObservation into a generic MemoryEntry."""
        session_id = obs.context_metadata.get("session_id")
        return MemoryEntry(
            id=f"wf_obs_{obs.execution_id}",
            content=f"Workflow observation for execution {obs.execution_id}",
            memory_type=MemoryType.WORKFLOW,
            metadata=MemoryMetadata(
                created_at=obs.timestamp,
                updated_at=obs.timestamp,
                source="workflow_observer",
                additional_info={
                    "user_id": obs.user_id,
                    "execution_id": obs.execution_id,
                    "sequence": obs.sequence.model_dump(),
                    "success": obs.success,
                    "context_metadata": obs.context_metadata,
                    "session_id": session_id,
                }
            )
        )

    def _to_observation(self, entry: MemoryEntry) -> WorkflowObservation:
        """Converts a generic MemoryEntry back into a WorkflowObservation."""
        info = entry.metadata.additional_info or {}
        return WorkflowObservation(
            user_id=info.get("user_id"),
            execution_id=info.get("execution_id"),
            sequence=WorkflowSequence(**info.get("sequence", {})),
            success=info.get("success"),
            timestamp=entry.metadata.created_at,
            context_metadata=info.get("context_metadata", {})
        )

    async def save(self, observation: WorkflowObservation) -> None:
        """Saves or updates a workflow observation."""
        entry = self._to_memory_entry(observation)
        existing = await self._provider.get(entry.id)
        if existing:
            await self._provider.update(entry.id, entry)
        else:
            await self._provider.save(entry)
        logger.debug("Workflow observation saved", extra={"execution_id": observation.execution_id})

    async def get(self, execution_id: str) -> Optional[WorkflowObservation]:
        """Retrieves a workflow observation by execution ID."""
        entry = await self._provider.get(f"wf_obs_{execution_id}")
        if entry:
            return self._to_observation(entry)
        return None

    async def list_by_session(self, session_id: str) -> List[WorkflowObservation]:
        """Retrieves all workflow observations matching a specific session ID."""
        query = MemoryQuery(
            text="",
            memory_type=MemoryType.WORKFLOW,
            filters={"session_id": session_id}
        )
        results = await self._provider.search(query)
        return [self._to_observation(r.entry) for r in results]

    async def list_by_user(self, user_id: int) -> List[WorkflowObservation]:
        """Retrieves all workflow observations matching a specific user ID."""
        query = MemoryQuery(
            text="",
            memory_type=MemoryType.WORKFLOW,
            filters={"user_id": user_id}
        )
        results = await self._provider.search(query)
        return [self._to_observation(r.entry) for r in results]

    async def delete(self, execution_id: str) -> None:
        """Deletes a workflow observation by execution ID."""
        await self._provider.delete(f"wf_obs_{execution_id}")
        logger.debug("Workflow observation deleted", extra={"execution_id": execution_id})

    async def cleanup(self, cutoff: datetime) -> int:
        """Deletes observations created prior to the specified cutoff datetime."""
        query = MemoryQuery(
            text="",
            memory_type=MemoryType.WORKFLOW
        )
        results = await self._provider.search(query)

        deleted_count = 0
        cutoff_aware = ensure_utc(cutoff)

        for r in results:
            entry = r.entry
            created_at = ensure_utc(entry.metadata.created_at)

            if created_at and created_at < cutoff_aware:
                await self._provider.delete(entry.id)
                deleted_count += 1

        logger.info("Cleanup completed", extra={"deleted_count": deleted_count, "cutoff": cutoff_aware.isoformat()})
        return deleted_count
