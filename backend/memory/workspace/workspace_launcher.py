"""User Workspace Launcher coordinating profile execution through Desktop Capability."""

import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WorkspaceLauncher:
    """Launches workspace configurations, setting env variables and executing apps through Desktop Capability."""

    def __init__(self, desktop_capability: Any) -> None:
        """Initializes WorkspaceLauncher.

        Args:
            desktop_capability: Injected DesktopCapability instance.
        """
        self._desktop_capability = desktop_capability

    def launch(self, settings: Dict[str, Any]) -> bool:
        """Restores and launches workspace resources using the desktop capability.

        Args:
            settings: The workspace profile settings dictionary.

        Returns:
            True if launch completed successfully, False otherwise.
        """
        logger.info("Starting workspace profile launch sequence.")

        # 1. Apply Environment Variables
        env_vars = settings.get("env_vars", {})
        for key, val in env_vars.items():
            logger.debug(f"Applying environment variable: {key}={val}")
            os.environ[key] = str(val)

        # 2. Extract configuration items
        apps = settings.get("applications", [])
        tabs = settings.get("browser_tabs", [])

        # 3. Determine Startup Sequence (default is apps then tabs)
        startup_order = settings.get("startup_order", ["applications", "browser_tabs"])

        for step in startup_order:
            if step == "applications":
                for app in apps:
                    app_name = app.get("name")
                    app_args = app.get("args", [])
                    logger.info(f"Workspace launching application: {app_name}")
                    self._desktop_capability.execute(
                        "OPEN_APPLICATION",
                        {"target": app_name, "arguments": app_args},
                    )
            elif step == "browser_tabs":
                for tab in tabs:
                    logger.info(f"Workspace launching browser tab: {tab}")
                    # Launches default browser using desktop capability
                    self._desktop_capability.execute(
                        "OPEN_APPLICATION",
                        {"target": "Microsoft Edge", "arguments": [tab]},
                    )

        logger.info("Workspace launch sequence completed successfully.")
        return True
