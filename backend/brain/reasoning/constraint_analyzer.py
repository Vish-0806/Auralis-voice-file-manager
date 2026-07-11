"""Constraint analyzer detecting system and runtime dependencies for Auralis."""

from __future__ import annotations

import logging
import os
import shutil
# pyrefly: ignore [missing-import]
from brain.goal.models import Goal
from .models import Constraint


class ConstraintAnalyzer:
    """Detects and validates requirements for a structured goal."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the ConstraintAnalyzer.

        Args:
            logger: Optional custom logger for constraint analysis.
        """
        self._logger = logger or logging.getLogger(__name__)

    def analyze_constraints(self, goal: Goal) -> list[Constraint]:
        """Analyzes a Goal and returns a list of system/runtime constraints.

        Args:
            goal: The Goal to analyze.

        Returns:
            A list of detected Constraints.
        """
        goal_name = goal.name.upper()
        constraints: list[Constraint] = []

        # 1. Internet dependency
        if goal_name in ["MEETING", "STUDY"]:
            satisfied = self._check_internet_connectivity()
            constraints.append(
                Constraint(
                    name="Internet Access",
                    type="internet",
                    description="Requires active internet connection to download/stream resources or join calls.",
                    satisfied=satisfied,
                )
            )

        # 2. Installed application dependency
        if goal_name == "START_CODING":
            has_ide = (
                shutil.which("code") is not None
                or os.path.exists(r"C:\Program Files\Microsoft VS Code\Code.exe")
                or os.path.exists(os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Microsoft VS Code\Code.exe"))
            )
            constraints.append(
                Constraint(
                    name="VS Code Installation",
                    type="application",
                    description="Visual Studio Code must be installed on the host system.",
                    satisfied=has_ide,
                )
            )
        elif goal_name == "OPEN_APPLICATION":
            app_name = goal.parameters.get("application")
            if app_name:
                has_app = self._check_app_installed(app_name)
                constraints.append(
                    Constraint(
                        name=f"Application '{app_name}' Installed",
                        type="application",
                        description=f"Desktop application '{app_name}' must be installed and resolvable on the host system.",
                        satisfied=has_app,
                    )
                )

        # 3. Permission requirements
        if goal_name in ["LOCK_COMPUTER", "CLEAN_WORKSPACE"]:
            constraints.append(
                Constraint(
                    name="OS Session Interaction Permission",
                    type="permission",
                    description="Requires permission to lock the workstation session or manage active windows.",
                    satisfied=True,
                )
            )

        # 4. File or folder requirements
        if goal_name == "ORGANIZE_DOWNLOADS":
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            has_downloads = os.path.isdir(downloads_path)
            constraints.append(
                Constraint(
                    name="Downloads Folder Existence",
                    type="file_system",
                    description="The host Downloads folder must exist and be readable.",
                    satisfied=has_downloads,
                )
            )

        self._logger.info(
            "Analyzed goal constraints",
            extra={"goal_name": goal.name, "constraints_count": len(constraints)},
        )
        return constraints

    def _check_internet_connectivity(self) -> bool:
        """Lightweight heuristic check for internet connectivity.

        Returns:
            True if connected, False otherwise.
        """
        import socket
        try:
            socket.setdefaulttimeout(1.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            self._logger.debug("Internet dependency check failed: Host is offline")
            return False

    def _check_app_installed(self, app_name: str) -> bool:
        """Heuristically checks if an application exists or is in PATH.

        Args:
            app_name: The name of the application.

        Returns:
            True if found or resolved, False otherwise.
        """
        if shutil.which(app_name):
            return True

        app_name_lower = app_name.lower()
        if "chrome" in app_name_lower:
            return (
                shutil.which("chrome") is not None
                or os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
                or os.path.exists(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
            )
        elif "code" in app_name_lower or "vs" in app_name_lower:
            return (
                shutil.which("code") is not None
                or os.path.exists(r"C:\Program Files\Microsoft VS Code\Code.exe")
                or os.path.exists(os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Microsoft VS Code\Code.exe"))
            )
        elif "notepad" in app_name_lower:
            return shutil.which("notepad") is not None or os.path.exists(r"C:\Windows\System32\notepad.exe")
        elif "calculator" in app_name_lower or "calc" in app_name_lower:
            return shutil.which("calc") is not None or os.path.exists(r"C:\Windows\System32\calc.exe")

        return True
