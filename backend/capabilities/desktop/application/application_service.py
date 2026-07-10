"""Application service coordinating path resolution and process management."""

from __future__ import annotations

import logging
import os
from .application_resolver import ApplicationResolver
from .process_manager import ProcessManager
from .models import ApplicationDetails


class ApplicationService:
    """Service to manage application operations (launch, close, restart, check running)."""

    # Default supported apps list to track casing and executable filenames
    SUPPORTED_APPS = [
        {"name": "Chrome", "executable": "chrome.exe"},
        {"name": "Microsoft Edge", "executable": "msedge.exe"},
        {"name": "Firefox", "executable": "firefox.exe"},
        {"name": "VS Code", "executable": "Code.exe"},
        {"name": "Notepad", "executable": "notepad.exe"},
        {"name": "Calculator", "executable": "calc.exe"},
        {"name": "Spotify", "executable": "Spotify.exe"},
        {"name": "Terminal", "executable": "wt.exe"},
    ]

    def __init__(
        self,
        resolver: ApplicationResolver | None = None,
        process_manager: ProcessManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ApplicationService.

        Args:
            resolver: Custom resolver.
            process_manager: Custom process manager.
            logger: Optional logger.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._resolver = resolver or ApplicationResolver(logger=self._logger)
        self._process_manager = process_manager or ProcessManager(logger=self._logger)

    def launch_application(self, app_name: str, arguments: list[str] | None = None) -> int:
        """Resolves path, validates, and launches the application.

        Args:
            app_name: Name of the application to launch.
            arguments: Optional CLI arguments.

        Returns:
            The process ID of the launched app.

        Raises:
            ValueError: If path resolution fails.
            FileNotFoundError: If the resolved path does not exist.
        """

        resolved_path = self._resolver.resolve(app_name)
        if not resolved_path:
            raise ValueError(f"Could not resolve executable path for application: '{app_name}'")

        if not os.path.exists(resolved_path) or not os.path.isfile(resolved_path):
            raise FileNotFoundError(f"Resolved path does not exist or is not a file: '{resolved_path}'")

        return self._process_manager.start_process(resolved_path, arguments)

    def close_application(self, app_name: str) -> bool:
        """Closes all running instances of the application.

        Args:
            app_name: Name of the application to close.

        Returns:
            True if any processes were terminated, False otherwise.
        """

        executable_name = self._get_executable_name(app_name)
        return self._process_manager.terminate_process(app_name, executable_name)

    def restart_application(self, app_name: str) -> int:
        """Gracefully terminates and then launches the application.

        Args:
            app_name: Name of the application.

        Returns:
            The PID of the newly launched process.
        """

        self.close_application(app_name)
        return self.launch_application(app_name)

    def is_running(self, app_name: str) -> bool:
        """Checks if the application is running.

        Args:
            app_name: Name of the application.

        Returns:
            True if running, False otherwise.
        """

        executable_name = self._get_executable_name(app_name)
        return self._process_manager.is_running(app_name, executable_name)

    def list_running_applications(self) -> list[ApplicationDetails]:
        """Lists running status and path for all supported applications.

        Returns:
            A list of ApplicationDetails.
        """

        results = []
        for app in self.SUPPORTED_APPS:
            name = app["name"]
            exec_name = app["executable"]
            resolved_path = self._resolver.resolve(name) or ""
            is_running = self._process_manager.is_running(name, exec_name)
            results.append(
                ApplicationDetails(
                    name=name,
                    executable_path=resolved_path,
                    is_running=is_running,
                )
            )
        return results

    def _get_executable_name(self, app_name: str) -> str | None:
        """Helper to find the executable filename from supported apps list."""

        normalized = app_name.strip().lower()
        for app in self.SUPPORTED_APPS:
            if app["name"].lower() == normalized or normalized in {
                "vscode",
                "vs code",
                "visual studio code",
            } and app["name"] == "VS Code":
                return app["executable"]
            if normalized in {"calc", "calculator"} and app["name"] == "Calculator":
                return app["executable"]
            if normalized in {"edge", "microsoft edge", "msedge"} and app["name"] == "Microsoft Edge":
                return app["executable"]
            if normalized in {"windows terminal", "terminal", "wt"} and app["name"] == "Terminal":
                return app["executable"]
        return None
