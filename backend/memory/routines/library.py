"""Routine Library catalogue management mapping definitions to repositories."""

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional
from memory.routines.models import RoutineDefinitionDomain

logger = logging.getLogger(__name__)


class RoutineLibrary:
    """Manages persistence registration, signatures, categorisation, and statistics."""

    def __init__(self, repository: Any) -> None:
        """Initializes the library catalogue with a repository interface."""
        self.repository = repository

    def register_routine(self, routine: RoutineDefinitionDomain) -> RoutineDefinitionDomain:
        """Saves a new routine definition, assigning runtime signatures and categories."""
        sig = "|".join([step.get("action") or step.get("intent") or "" for step in routine.steps])
        routine.metadata_info["signature"] = sig
        routine.metadata_info["version_history"] = [
            {"version": routine.version, "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
        if "category" not in routine.metadata_info:
            routine.metadata_info["category"] = "general"
        if "tags" not in routine.metadata_info:
            routine.metadata_info["tags"] = []

        saved = self.repository.create(routine)
        logger.info(f"Registered routine: '{routine.name}' with ID {saved.id}")
        return saved

    def delete_routine(self, routine_id: int) -> bool:
        """Deletes a routine definition by ID."""
        logger.info(f"Deleting routine definition ID {routine_id}")
        return self.repository.delete(routine_id)

    def update_routine(self, routine_id: int, routine: RoutineDefinitionDomain) -> Optional[RoutineDefinitionDomain]:
        """Updates a routine definition, incrementing version numbers and recording history."""
        existing = self.repository.get_by_id(routine_id)
        if not existing:
            return None

        routine.id = routine_id
        routine.version = existing.version + 1
        history = list(existing.metadata_info.get("version_history", []))
        history.append({"version": routine.version, "timestamp": datetime.now(timezone.utc).isoformat()})
        routine.metadata_info["version_history"] = history

        updated = self.repository.update(routine_id, routine)
        logger.info(f"Updated routine definition ID {routine_id} to version {routine.version}")
        return updated

    def get_routine(self, routine_id: int) -> Optional[RoutineDefinitionDomain]:
        """Gets a routine definition by ID."""
        return self.repository.get_by_id(routine_id)

    def list_routines(self, filters: Optional[dict] = None) -> List[RoutineDefinitionDomain]:
        """Lists and searches routine definitions matching query filters."""
        return self.repository.search(filters or {})
