"""User Workspace Configuration Validator."""

from typing import Any, Dict
from memory.workspace.workspace_models import InvalidWorkspaceError


class WorkspaceValidator:
    """Validates the schema structure of workspace profile settings bags."""

    @staticmethod
    def validate_settings(settings: Dict[str, Any]) -> None:
        """Validates a workspace profile settings dictionary against schema layout rules.

        Args:
            settings: Dictionary payload to check.

        Raises:
            InvalidWorkspaceError: If structure or schema type constraint fails.
        """
        # Validate applications
        apps = settings.get("applications", [])
        if not isinstance(apps, list):
            raise InvalidWorkspaceError("Workspace settings 'applications' field must be a list.")
        for idx, app in enumerate(apps):
            if not isinstance(app, dict) or "name" not in app:
                raise InvalidWorkspaceError(
                    f"Application entry at index {idx} must be a dictionary containing a 'name' string key."
                )
            if not isinstance(app["name"], str):
                raise InvalidWorkspaceError(f"Application 'name' at index {idx} must be a string.")

        # Validate projects
        projects = settings.get("projects", [])
        if not isinstance(projects, list):
            raise InvalidWorkspaceError("Workspace settings 'projects' field must be a list of paths.")
        for idx, path in enumerate(projects):
            if not isinstance(path, str):
                raise InvalidWorkspaceError(f"Project directory path at index {idx} must be a string.")

        # Validate browser tabs
        tabs = settings.get("browser_tabs", [])
        if not isinstance(tabs, list):
            raise InvalidWorkspaceError("Workspace settings 'browser_tabs' field must be a list.")
        for idx, url in enumerate(tabs):
            if not isinstance(url, str):
                raise InvalidWorkspaceError(f"Browser tab URL path at index {idx} must be a string.")

        # Validate terminal configuration
        term = settings.get("terminal_config", {})
        if not isinstance(term, dict):
            raise InvalidWorkspaceError("Workspace settings 'terminal_config' must be a dictionary.")

        # Validate environment variables
        env = settings.get("env_vars", {})
        if not isinstance(env, dict):
            raise InvalidWorkspaceError("Workspace settings 'env_vars' must be a dictionary.")

        # Validate startup order
        order = settings.get("startup_order", [])
        if not isinstance(order, list):
            raise InvalidWorkspaceError("Workspace settings 'startup_order' must be a list.")
        for idx, ord_item in enumerate(order):
            if not isinstance(ord_item, str):
                raise InvalidWorkspaceError(f"Startup order item at index {idx} must be a string.")
