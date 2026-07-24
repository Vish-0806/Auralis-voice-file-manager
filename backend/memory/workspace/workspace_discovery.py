"""Workspace Discovery Engine for detecting project and repository roots on disk."""

import os
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkspaceDiscoveryConfig(BaseModel):
    """Configuration options for filesystem workspace discovery."""

    max_depth: int = Field(default=5, description="Maximum recursion depth for filesystem scans.")
    ignored_folders: List[str] = Field(
        default_factory=lambda: [".git", "node_modules", "venv", "__pycache__", "build", "dist", "target"],
        description="Folders to completely skip during traversal."
    )
    max_projects: int = Field(default=100, description="Maximum number of projects to detect before stopping.")
    scan_timeout: float = Field(default=30.0, description="Absolute timeout in seconds for filesystem scans.")
    allowed_roots: List[str] = Field(default_factory=list, description="Explicit whitelist of scan root paths.")


class WorkspaceDiscoveryResult(BaseModel):
    """The outcome metadata representing a discovered workspace/project root."""

    workspace_path: str = Field(description="Full physical directory path on disk.")
    project_name: str = Field(description="Detected name of the project folder.")
    detection_reason: str = Field(description="Explanation of why this path was classified as a workspace root.")
    confidence: float = Field(default=1.0, description="Classification confidence score between 0.0 and 1.0.")
    last_modified: datetime = Field(description="Timestamp indicating when the project files were last updated.")


class WorkspaceDiscoveryEngine:
    """Discovers project directories, build roots, and repositories within search parameters."""

    def __init__(self, config: Optional[WorkspaceDiscoveryConfig] = None) -> None:
        """Initializes the WorkspaceDiscoveryEngine.

        Args:
            config: Optional WorkspaceDiscoveryConfig instance.
        """
        self.config = config or WorkspaceDiscoveryConfig()

    async def discover(self, search_root: str) -> List[WorkspaceDiscoveryResult]:
        """Scans the directory tree starting at search_root to discover candidates.

        Args:
            search_root: The root filesystem directory to start scanning from.

        Returns:
            A list of WorkspaceDiscoveryResult models representing detected projects.
        """
        normalized_root = os.path.abspath(search_root)

        # 1. Verification of whitelist allowed_roots constraints
        if self.config.allowed_roots:
            allowed = False
            for root in self.config.allowed_roots:
                norm_allowed = os.path.abspath(root)
                # Check if search_root matches prefix of any whitelisted allowed roots
                if normalized_root.startswith(norm_allowed):
                    allowed = True
                    break
            if not allowed:
                logger.warning(f"Scan path {normalized_root} is not whitelisted in allowed_roots.")
                return []

        if not os.path.isdir(normalized_root):
            logger.warning(f"Scan root path {normalized_root} is not a valid directory.")
            return []

        results: List[WorkspaceDiscoveryResult] = []
        start_time = time.time()

        # Workspace detection markers
        folder_markers = {".git", ".vscode"}
        file_markers = {
            "package.json",
            "Cargo.toml",
            "requirements.txt",
            "pyproject.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
        }

        # Synchronous traversal helper run in a background executor thread
        def _scan_directory(path: str, depth: int) -> None:
            # Check timeout limit
            if time.time() - start_time > self.config.scan_timeout:
                logger.warning(f"Filesystem scan timed out after {self.config.scan_timeout}s.")
                return

            # Check max projects counter
            if len(results) >= self.config.max_projects:
                return

            # Check maximum depth bounds
            if depth > self.config.max_depth:
                return

            try:
                entries = os.listdir(path)
            except PermissionError:
                logger.warning(f"Permission denied accessing directory: {path}")
                return
            except Exception as e:
                logger.error(f"Error accessing directory {path}: {e}")
                return

            entry_set = set(entries)

            # A. Check for Git repository (highest priority, confidence 1.0)
            if ".git" in entry_set:
                git_path = os.path.join(path, ".git")
                try:
                    last_mod = datetime.fromtimestamp(os.path.getmtime(git_path), timezone.utc)
                except Exception:
                    last_mod = datetime.now(timezone.utc)

                results.append(
                    WorkspaceDiscoveryResult(
                        workspace_path=path,
                        project_name=os.path.basename(path),
                        detection_reason="Found Git repository marker (.git directory)",
                        confidence=1.0,
                        last_modified=last_mod,
                    )
                )
                # Terminate deeper recursion into project subdirectory to avoid duplication
                return

            # B. Check for build system configuration files (confidence 0.9)
            matched_marker = None
            found_folders = entry_set.intersection(folder_markers)
            if found_folders:
                matched_marker = next(iter(found_folders))
            else:
                found_files = entry_set.intersection(file_markers)
                if found_files:
                    matched_marker = next(iter(found_files))

            if matched_marker:
                marker_path = os.path.join(path, matched_marker)
                try:
                    last_mod = datetime.fromtimestamp(os.path.getmtime(marker_path), timezone.utc)
                except Exception:
                    last_mod = datetime.now(timezone.utc)

                results.append(
                    WorkspaceDiscoveryResult(
                        workspace_path=path,
                        project_name=os.path.basename(path),
                        detection_reason=f"Found build/IDE project marker ({matched_marker})",
                        confidence=0.9,
                        last_modified=last_mod,
                    )
                )
                # Terminate recursion
                return

            # C. Traverse nested directories (if not matched or ignored)
            for entry in entries:
                if entry in self.config.ignored_folders:
                    continue

                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    # Prevent circular symlink recursion loops
                    if os.path.islink(full_path):
                        continue
                    _scan_directory(full_path, depth + 1)

        # Run filesystem I/O off the main thread to avoid blocking the event loop
        await asyncio.to_thread(_scan_directory, normalized_root, 0)
        return results
