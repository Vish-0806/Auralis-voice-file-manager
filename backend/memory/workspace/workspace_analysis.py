"""Workspace Analysis Domain Model containing unified workspace findings."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkspaceAnalysis(BaseModel):
    """Unified domain model representing a completed filesystem and project analysis."""

    workspace_path: str = Field(description="Root path of the indexed workspace.")
    project_name: str = Field(description="Name of the project folder.")
    project_type: str = Field(description="Classified project type (e.g. node, rust, python, none).")
    repository_type: str = Field(description="Version control repository classification (e.g. git, none).")
    dominant_language: str = Field(description="Programming language with the highest total byte weight.")
    language_statistics: Dict[str, float] = Field(description="Map of programming languages to size percentage.")
    language_counts: Dict[str, int] = Field(description="Map of programming languages to file count.")
    build_system: Optional[str] = Field(default=None, description="Detected build system tool name.")
    recommended_build_command: Optional[str] = Field(default=None, description="Suggested command to execute a build.")
    git_branch: Optional[str] = Field(default=None, description="Current checked out Git branch name.")
    git_remote_available: bool = Field(default=False, description="True if a Git remote URL is configured.")
    git_dirty: bool = Field(default=False, description="True if local uncommitted files exist.")
    git_has_unpushed_commits: bool = Field(default=False, description="True if there are local commits not pushed to remote.")
    total_files: int = Field(description="Total count of files indexed in workspace.")
    total_directories: int = Field(description="Total count of subfolders indexed.")
    maximum_depth: int = Field(description="Maximum directory nesting depth traversed.")
    total_size: int = Field(description="Total size in bytes of all indexed files.")
    last_indexed: datetime = Field(description="Timestamp indicating when the index was compiled.")
    analysis_timestamp: datetime = Field(description="Timestamp indicating when analysis was completed.")

    def is_git_repository(self) -> bool:
        """Checks if the workspace is configured as a Git repository."""
        return self.repository_type == "git"

    def is_python_project(self) -> bool:
        """Checks if the project type classification is Python."""
        return self.project_type == "python"

    def is_node_project(self) -> bool:
        """Checks if the project type classification is Node."""
        return self.project_type == "node"

    def is_java_project(self) -> bool:
        """Checks if the project type classification is Java."""
        return self.project_type == "java"

    def summary(self) -> str:
        """Generates a detailed human-readable summary string of workspace findings."""
        git_info = "N/A"
        if self.is_git_repository():
            git_info = f"Branch: {self.git_branch or 'unknown'}, Dirty: {self.git_dirty}, Remote: {self.git_remote_available}"

        build_info = "None"
        if self.build_system:
            build_info = f"Build System: {self.build_system}, Recommended Command: '{self.recommended_build_command}'"

        lang_breakdown = ", ".join(
            f"{lang}: {pct*100:.1f}%"
            for lang, pct in sorted(self.language_statistics.items(), key=lambda x: x[1], reverse=True)
        )
        if not lang_breakdown:
            lang_breakdown = "None"

        summary_text = (
            f"Workspace Path: {self.workspace_path}\n"
            f"Project Name: {self.project_name} ({self.project_type.upper()})\n"
            f"Dominant Language: {self.dominant_language}\n"
            f"Languages: {lang_breakdown}\n"
            f"Build: {build_info}\n"
            f"Git: {git_info}\n"
            f"Filesystem: {self.total_files} files, {self.total_directories} directories, Size: {self.total_size} bytes (depth limit reached: {self.maximum_depth})"
        )
        return summary_text
