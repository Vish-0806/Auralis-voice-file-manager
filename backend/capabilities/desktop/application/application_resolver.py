"""Module to resolve application names to their executable paths."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path


class ApplicationResolver:
    """Resolves application names to their executable paths on the host OS.

    Supports custom overrides and environment-aware default search paths for
    Chrome, Microsoft Edge, Firefox, VS Code, Notepad, Calculator, Spotify, and Terminal.
    """

    def __init__(
        self,
        custom_mappings: dict[str, str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the ApplicationResolver.

        Args:
            custom_mappings: Optional directory of manual name-to-path mappings.
            logger: Optional logger for path resolution.
        """

        self._logger = logger or logging.getLogger(__name__)
        self._custom_mappings = {k.lower(): v for k, v in (custom_mappings or {}).items()}

    def resolve(self, app_name: str) -> str | None:
        """Resolves an application name to its absolute executable path.

        Args:
            app_name: The name of the application (e.g., 'Chrome', 'VS Code').

        Returns:
            The resolved executable path if found, otherwise None.
        """

        key = app_name.strip().lower()

        # Check custom override mappings first
        if key in self._custom_mappings:
            path = self._custom_mappings[key]
            self._logger.debug(
                "Resolved app via custom mapping",
                extra={"app_name": app_name, "path": path},
            )
            return path

        # Standard resolution candidates
        candidates = self._get_candidates(key)
        for path_str in candidates:
            if not path_str:
                continue
            # Expand environment variables
            expanded = os.path.expandvars(path_str)
            if os.path.exists(expanded) and os.path.isfile(expanded):
                self._logger.debug(
                    "Resolved app via candidate check",
                    extra={"app_name": app_name, "path": expanded},
                )
                return os.path.abspath(expanded)

        # Fallback to shutil.which in case it is on PATH
        path_on_path = self._resolve_from_path(key)
        if path_on_path:
            self._logger.debug(
                "Resolved app via system PATH",
                extra={"app_name": app_name, "path": path_on_path},
            )
            return path_on_path

        self._logger.warning("Could not resolve application", extra={"app_name": app_name})
        return None

    def _get_candidates(self, key: str) -> list[str]:
        """Returns the list of path candidates for a normalized key."""

        pf = os.environ.get("ProgramFiles", "C:\\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app = os.environ.get("LocalAppData", "C:\\Users\\Default\\AppData\\Local")
        app_data = os.environ.get("APPDATA", "C:\\Users\\Default\\AppData\\Roaming")
        sys_root = os.environ.get("SystemRoot", "C:\\Windows")

        if key in {"chrome", "google chrome"}:
            return [
                rf"{pf}\Google\Chrome\Application\chrome.exe",
                rf"{pf86}\Google\Chrome\Application\chrome.exe",
                rf"{local_app}\Google\Chrome\Application\chrome.exe",
            ]
        if key in {"microsoft edge", "edge", "msedge"}:
            return [
                rf"{pf86}\Microsoft\Edge\Application\msedge.exe",
                rf"{pf}\Microsoft\Edge\Application\msedge.exe",
            ]
        if key == "firefox":
            return [
                rf"{pf}\Mozilla Firefox\firefox.exe",
                rf"{pf86}\Mozilla Firefox\firefox.exe",
            ]
        if key in {"vs code", "vscode", "visual studio code"}:
            return [
                rf"{local_app}\Programs\Microsoft VS Code\Code.exe",
                rf"{pf}\Microsoft VS Code\Code.exe",
            ]
        if key == "notepad":
            return [
                rf"{sys_root}\System32\notepad.exe",
                rf"{sys_root}\notepad.exe",
            ]
        if key in {"calculator", "calc"}:
            return [
                rf"{sys_root}\System32\calc.exe",
            ]
        if key == "spotify":
            return [
                rf"{app_data}\Spotify\Spotify.exe",
                rf"{local_app}\Spotify\Spotify.exe",
                rf"{pf}\Spotify\Spotify.exe",
            ]
        if key in {"terminal", "windows terminal", "wt"}:
            return [
                rf"{local_app}\Microsoft\WindowsApps\wt.exe",
                rf"{sys_root}\System32\cmd.exe",
            ]

        return []

    def _resolve_from_path(self, key: str) -> str | None:
        """Attempts to resolve the command name using shutil.which."""

        command_map = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "microsoft edge": "msedge",
            "edge": "msedge",
            "msedge": "msedge",
            "firefox": "firefox",
            "vs code": "code",
            "vscode": "code",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "spotify": "spotify",
            "terminal": "wt",
            "windows terminal": "wt",
            "wt": "wt",
        }

        cmd = command_map.get(key)
        if cmd:
            resolved = shutil.which(cmd)
            if resolved:
                return os.path.abspath(resolved)
        return None
