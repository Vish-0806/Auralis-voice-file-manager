"""User Workspace Snapshot capture utility."""

import time
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class WorkspaceSnapshot:
    """Utility to capture a snapshot of the current workspace state from context and OS capabilities."""

    @staticmethod
    def capture(
        user_id: int,
        session_id: str,
        context_service: Any,
        desktop_capability: Any,
    ) -> Dict[str, Any]:
        """Queries running systems and active contexts to build a workspace settings snapshot payload.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.
            context_service: Injected ContextService instance.
            desktop_capability: Injected DesktopCapability instance.

        Returns:
            Dictionary containing 'path' and 'settings' for a new WorkspaceProfile.
        """
        logger.info("Capturing user workspace snapshot.")

        # 1. Pull active path from ContextService
        ctx = context_service.load(user_id, session_id)
        workspace_path = ctx.get("active_workspace", ctx.get("current_project", "/workspace"))

        # 2. Query open windows via Desktop Capability
        apps = []
        try:
            res = desktop_capability.execute("LIST_WINDOWS", {})
            # If the desktop capability successfully returned running windows
            if isinstance(res, dict) and res.get("success"):
                windows = res.get("data", {}).get("windows", [])
                seen = set()
                for w in windows:
                    app_name = w.get("owner") or w.get("title")
                    if app_name and app_name not in seen:
                        seen.add(app_name)
                        apps.append({"name": app_name, "args": []})
        except Exception as e:
            logger.warning(f"Failed to query running windows for snapshot: {e}")

        # If no active apps were found, provide fallback placeholders
        if not apps:
            apps = [{"name": "VS Code", "args": []}]

        # 3. Assemble snapshot structure
        settings = {
            "applications": apps,
            "projects": [workspace_path] if workspace_path else [],
            "browser_tabs": [],
            "terminal_config": {},
            "env_vars": {},
            "startup_order": ["applications"],
            "metadata": {
                "description": f"Snapshot captured at {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "tags": ["snapshot"],
            },
        }

        return {
            "path": workspace_path,
            "settings": settings,
        }
    
    @staticmethod
    def capture_and_save(
        user_id: int,
        session_id: str,
        profile_name: str,
        context_service: Any,
        desktop_capability: Any,
        workspace_service: Any,
    ) -> Any:
        """Helper to capture the current state and persist it as a new profile.

        Args:
            user_id: Owner user identifier.
            session_id: Active session identifier.
            profile_name: Desired name for the new profile.
            context_service: ContextService instance.
            desktop_capability: DesktopCapability instance.
            workspace_service: WorkspaceService instance.

        Returns:
            The saved WorkspaceProfileDomain object.
        """
        snapshot_data = WorkspaceSnapshot.capture(
            user_id=user_id,
            session_id=session_id,
            context_service=context_service,
            desktop_capability=desktop_capability,
        )
        return workspace_service.create(
            user_id=user_id,
            name=profile_name,
            path=snapshot_data["path"],
            settings=snapshot_data["settings"],
        )
