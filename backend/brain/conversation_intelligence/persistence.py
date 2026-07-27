"""Handles database-agnostic persistence for dialogue states and history logs."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from memory import MemoryService
from memory.models.domain_models import MemoryEntry, MemoryType, MemoryMetadata
from brain.conversation_intelligence.models import DialogueState, DialogueHistory

logger = logging.getLogger(__name__)


class DialoguePersistenceManager:
    """Uses MemoryService to save and retrieve dialogue context models."""

    def __init__(self, memory_service: MemoryService) -> None:
        self._memory_service = memory_service

    def _run_sync(self, coro: Any) -> Any:
        """Helper to run a coroutine synchronously without event loop deadlocks."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import threading
            result_container = []
            exception_container = []

            def worker():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    res = new_loop.run_until_complete(coro)
                    result_container.append(res)
                    new_loop.close()
                except Exception as ex:
                    exception_container.append(ex)

            t = threading.Thread(target=worker)
            t.start()
            t.join()
            if exception_container:
                raise exception_container[0]
            return result_container[0]
        else:
            return loop.run_until_complete(coro)

    def save_state(self, state: DialogueState) -> None:
        """Saves a DialogueState to persistence."""
        entry_id = f"dialogue_state_{state.session_id}"
        entry = MemoryEntry(
            id=entry_id,
            content=state.json(),
            memory_type=MemoryType.SESSION,
            metadata=MemoryMetadata(
                tags=["dialogue_state"],
                additional_info={"session_id": state.session_id},
            ),
        )
        self._run_sync(self._memory_service.save(entry))
        logger.info("Saved dialogue state to database for session %s", state.session_id)

    def load_state(self, session_id: str) -> Optional[DialogueState]:
        """Loads a DialogueState from persistence."""
        entry_id = f"dialogue_state_{session_id}"
        try:
            entry = self._run_sync(self._memory_service.get(entry_id))
            if entry and entry.content:
                data = json.loads(entry.content)
                return DialogueState.parse_obj(data)
        except Exception as e:
            logger.warning("Failed to load dialogue state for session %s: %s", session_id, e)
        return None

    def delete_state(self, session_id: str) -> None:
        """Deletes DialogueState from persistence."""
        entry_id = f"dialogue_state_{session_id}"
        try:
            self._run_sync(self._memory_service.delete(entry_id))
            logger.info("Deleted dialogue state for session %s", session_id)
        except Exception as e:
            logger.warning("Failed to delete dialogue state for session %s: %s", session_id, e)

    def save_history(self, history: DialogueHistory) -> None:
        """Saves a DialogueHistory to persistence."""
        entry_id = f"dialogue_history_{history.session_id}"
        entry = MemoryEntry(
            id=entry_id,
            content=history.json(),
            memory_type=MemoryType.CONVERSATION,
            metadata=MemoryMetadata(
                tags=["dialogue_history"],
                additional_info={"session_id": history.session_id},
            ),
        )
        self._run_sync(self._memory_service.save(entry))
        logger.info("Saved dialogue history to database for session %s", history.session_id)

    def load_history(self, session_id: str) -> Optional[DialogueHistory]:
        """Loads a DialogueHistory from persistence."""
        entry_id = f"dialogue_history_{session_id}"
        try:
            entry = self._run_sync(self._memory_service.get(entry_id))
            if entry and entry.content:
                data = json.loads(entry.content)
                return DialogueHistory.parse_obj(data)
        except Exception as e:
            logger.warning("Failed to load dialogue history for session %s: %s", session_id, e)
        return None

    def delete_history(self, session_id: str) -> None:
        """Deletes DialogueHistory from persistence."""
        entry_id = f"dialogue_history_{session_id}"
        try:
            self._run_sync(self._memory_service.delete(entry_id))
            logger.info("Deleted dialogue history for session %s", session_id)
        except Exception as e:
            logger.warning("Failed to delete dialogue history for session %s: %s", session_id, e)
