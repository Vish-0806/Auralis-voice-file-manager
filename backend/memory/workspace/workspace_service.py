"""User Workspace Service public interface module."""

import logging
from typing import Any, Dict, List, Optional

from memory.models.domain_models import WorkspaceProfileDomain
from memory.workspace.workspace_manager import WorkspaceManager
from memory.workspace.workspace_launcher import WorkspaceLauncher
from memory.workspace.workspace_snapshot import WorkspaceSnapshot

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Sole public gateway/API for all Workspace Profile operations in Auralis."""

    def __init__(
        self,
        manager: Optional[WorkspaceManager] = None,
        launcher: Optional[WorkspaceLauncher] = None,
        desktop_capability: Optional[Any] = None,
    ) -> None:
        """Initializes the WorkspaceService.

        If collaborators are omitted, resolves them dynamically via SessionLocal,
        WorkspaceRepository, and DesktopCapability.

        Args:
            manager: Optional custom WorkspaceManager instance.
            launcher: Optional custom WorkspaceLauncher instance.
            desktop_capability: Optional custom DesktopCapability instance.
        """
        self._desktop_capability = desktop_capability
        if self._desktop_capability is None:
            try:
                from capabilities.desktop.desktop_capability import DesktopCapability
                self._desktop_capability = DesktopCapability()
            except Exception:
                logger.warning("Could not resolve default DesktopCapability. Launches will be logged only.")
                self._desktop_capability = None

        if manager is not None:
            self._manager = manager
        else:
            from memory.database.session import SessionLocal
            from memory.repository.workspace_repository import WorkspaceRepository

            self._db = SessionLocal()
            repository = WorkspaceRepository(self._db)
            self._manager = WorkspaceManager(repository)

        if launcher is not None:
            self._launcher = launcher
        else:
            self._launcher = WorkspaceLauncher(self._desktop_capability)

    def __del__(self) -> None:
        """Ensures the internal database session is closed correctly when garbage collected."""
        if hasattr(self, "_db"):
            try:
                self._db.close()
            except Exception:
                pass

    def create(
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
        """
        return self._manager.create_workspace(user_id, name, path, settings)

    def get(self, user_id: int, profile_id: int) -> WorkspaceProfileDomain:
        """Retrieves a workspace profile by ID.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.

        Returns:
            The WorkspaceProfileDomain object.
        """
        return self._manager.get_workspace(user_id, profile_id)

    def get_by_name(self, user_id: int, name: str) -> WorkspaceProfileDomain:
        """Retrieves a workspace profile by name.

        Args:
            user_id: Owner user identifier.
            name: Profile name.

        Returns:
            The WorkspaceProfileDomain object.
        """
        return self._manager.get_workspace_by_name(user_id, name)

    def update(
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
        """
        return self._manager.update_workspace(user_id, profile_id, path, settings)

    def delete(self, user_id: int, profile_id: int) -> bool:
        """Deletes a workspace profile.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.

        Returns:
            True if deleted, False if not found.
        """
        return self._manager.delete_workspace(user_id, profile_id)

    def duplicate(self, user_id: int, profile_id: int, new_name: str) -> WorkspaceProfileDomain:
        """Duplicates an existing workspace profile under a new name.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile ID to copy.
            new_name: New profile name.

        Returns:
            The newly created WorkspaceProfileDomain object.
        """
        return self._manager.duplicate_workspace(user_id, profile_id, new_name)

    def list(self, user_id: int) -> List[WorkspaceProfileDomain]:
        """Lists all workspace profiles for a user.

        Args:
            user_id: Owner user identifier.

        Returns:
            List of WorkspaceProfileDomain objects.
        """
        return self._manager.list_workspaces(user_id)

    def get_template(self, name: str) -> Dict[str, Any]:
        """Retrieves config template settings for a built-in workspace category.

        Args:
            name: Template name (e.g. 'coding', 'study').

        Returns:
            Dictionary payload config containing 'path' and 'settings' keys.
        """
        return self._manager.get_template(name)

    def restore(self, user_id: int, profile_id: int) -> bool:
        """Restores and launches workspace resources using the desktop capability.

        Args:
            user_id: Owner user identifier.
            profile_id: Profile primary identifier.

        Returns:
            True if launch completed successfully, False otherwise.
        """
        profile = self.get(user_id, profile_id)
        return self._launcher.launch(profile.settings)

    def snapshot(
        self,
        user_id: int,
        session_id: str,
        profile_name: str,
        context_service: Any,
    ) -> WorkspaceProfileDomain:
        """Captures the current active context and processes and saves them as a new profile.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.
            profile_name: Desired name for the new profile.
            context_service: ContextService instance.

        Returns:
            The saved WorkspaceProfileDomain object.
        """
        return WorkspaceSnapshot.capture_and_save(
            user_id=user_id,
            session_id=session_id,
            profile_name=profile_name,
            context_service=context_service,
            desktop_capability=self._desktop_capability,
            workspace_service=self,
        )
