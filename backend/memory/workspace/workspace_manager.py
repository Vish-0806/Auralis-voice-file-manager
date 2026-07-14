"""Workspace profile manager implementation."""

import logging
from typing import Any, Dict, List, Optional

from memory.models.domain_models import WorkspaceProfileDomain
from memory.repository.workspace_repository import WorkspaceRepository
from memory.workspace.workspace_validator import WorkspaceValidator
from memory.workspace.workspace_models import (
    WORKSPACE_TEMPLATES,
    WorkspaceError,
    InvalidWorkspaceError,
    WorkspaceNotFoundError,
)

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages User Workspace Profiles CRUD, Duplication, and Template resolution."""

    def __init__(
        self,
        repository: WorkspaceRepository,
        validator: Optional[WorkspaceValidator] = None,
    ) -> None:
        """Initializes WorkspaceManager with dependencies.

        Args:
            repository: Workspace database repository collaborator.
            validator: Optional custom validator.
        """
        self._repository = repository
        self._validator = validator or WorkspaceValidator()

    def create_workspace(
        self,
        user_id: int,
        name: str,
        path: str,
        settings: Dict[str, Any],
    ) -> WorkspaceProfileDomain:
        """Validates and persists a new workspace profile.

        Args:
            user_id: Owner user identifier.
            name: Profile name.
            path: Workspace root path.
            settings: Setup options.

        Returns:
            The saved WorkspaceProfileDomain object.

        Raises:
            InvalidWorkspaceError: If validation fails.
            WorkspaceError: If a duplicate profile name exists for the user.
        """
        if not name or not name.strip():
            raise InvalidWorkspaceError("Workspace profile name cannot be empty.")
        if not path or not path.strip():
            raise InvalidWorkspaceError("Workspace root directory path cannot be empty.")

        self._validator.validate_settings(settings)

        # Check for duplicates
        existing = self._repository.search({"user_id": user_id, "name": name})
        if existing:
            raise WorkspaceError(f"Workspace profile '{name}' already exists for user {user_id}.")

        logger.info(
            "Creating workspace profile",
            extra={"user_id": user_id, "name": name, "path": path},
        )
        domain = WorkspaceProfileDomain(
            user_id=user_id,
            name=name,
            path=path,
            settings=settings,
        )
        return self._repository.create(domain)

    def get_workspace(self, user_id: int, profile_id: int) -> WorkspaceProfileDomain:
        """Retrieves a workspace profile by ID.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.

        Returns:
            The WorkspaceProfileDomain object.

        Raises:
            WorkspaceNotFoundError: If not found or belongs to another user.
        """
        profile = self._repository.get_by_id(profile_id)
        if profile is None or profile.user_id != user_id:
            raise WorkspaceNotFoundError(f"Workspace profile with ID {profile_id} was not found.")
        return profile

    def get_workspace_by_name(self, user_id: int, name: str) -> WorkspaceProfileDomain:
        """Retrieves a workspace profile by name.

        Args:
            user_id: Owner user identifier.
            name: Profile name.

        Returns:
            The WorkspaceProfileDomain object.

        Raises:
            WorkspaceNotFoundError: If not found.
        """
        profiles = self._repository.search({"user_id": user_id, "name": name})
        if not profiles:
            raise WorkspaceNotFoundError(f"Workspace profile with name '{name}' was not found.")
        return profiles[0]

    def update_workspace(
        self,
        user_id: int,
        profile_id: int,
        path: str,
        settings: Dict[str, Any],
    ) -> WorkspaceProfileDomain:
        """Updates an existing workspace profile.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.
            path: Updated workspace root path.
            settings: Updated setup options.

        Returns:
            The updated WorkspaceProfileDomain object.

        Raises:
            WorkspaceNotFoundError: If the profile is not found.
            InvalidWorkspaceError: If validation fails.
        """
        profile = self.get_workspace(user_id, profile_id)

        if not path or not path.strip():
            raise InvalidWorkspaceError("Workspace root directory path cannot be empty.")

        self._validator.validate_settings(settings)

        logger.info(
            "Updating workspace profile",
            extra={"user_id": user_id, "profile_id": profile_id, "path": path},
        )
        profile.path = path
        profile.settings = settings

        updated = self._repository.update(profile_id, profile)
        if updated is None:
            raise WorkspaceNotFoundError(f"Failed to update workspace profile with ID {profile_id}.")
        return updated

    def delete_workspace(self, user_id: int, profile_id: int) -> bool:
        """Deletes a workspace profile.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.

        Returns:
            True if deleted, False if not found.
        """
        try:
            profile = self.get_workspace(user_id, profile_id)
        except WorkspaceNotFoundError:
            return False

        logger.info(
            "Deleting workspace profile",
            extra={"user_id": user_id, "profile_id": profile_id},
        )
        return self._repository.delete(profile.id)

    def duplicate_workspace(self, user_id: int, profile_id: int, new_name: str) -> WorkspaceProfileDomain:
        """Duplicates an existing workspace profile under a new name.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile ID to copy.
            new_name: New profile name.

        Returns:
            The newly created WorkspaceProfileDomain object.

        Raises:
            WorkspaceNotFoundError: If target profile is not found.
            WorkspaceError: If duplicate profile name exists.
        """
        target = self.get_workspace(user_id, profile_id)

        # Duplicate check
        existing = self._repository.search({"user_id": user_id, "name": new_name})
        if existing:
            raise WorkspaceError(f"Workspace profile '{new_name}' already exists for user {user_id}.")

        logger.info(
            "Duplicating workspace profile",
            extra={"user_id": user_id, "source_id": profile_id, "new_name": new_name},
        )
        return self.create_workspace(user_id, new_name, target.path, target.settings)

    def list_workspaces(self, user_id: int) -> List[WorkspaceProfileDomain]:
        """Lists all workspace profiles for a user.

        Args:
            user_id: Owner user identifier.

        Returns:
            List of WorkspaceProfileDomain objects.
        """
        return self._repository.search({"user_id": user_id})

    def get_template(self, name: str) -> Dict[str, Any]:
        """Retrieves config template settings for a built-in workspace category.

        Args:
            name: Template name (e.g. 'coding', 'study').

        Returns:
            Dictionary payload config containing 'path' and 'settings' keys.

        Raises:
            WorkspaceNotFoundError: If the template name is not found.
        """
        name_lower = name.lower()
        if name_lower not in WORKSPACE_TEMPLATES:
            raise WorkspaceNotFoundError(f"Built-in workspace template '{name}' was not found.")
        return WORKSPACE_TEMPLATES[name_lower]
