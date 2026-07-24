"""Unified entry point for the Workspace Profiles subsystem."""

from memory.workspace.workspace_service import WorkspaceService
from memory.workspace.workspace_manager import WorkspaceManager
from memory.workspace.workspace_validator import WorkspaceValidator
from memory.workspace.workspace_launcher import WorkspaceLauncher
from memory.workspace.workspace_snapshot import WorkspaceSnapshot
from memory.workspace.workspace_discovery import (
    WorkspaceDiscoveryEngine,
    WorkspaceDiscoveryConfig,
    WorkspaceDiscoveryResult,
)
from memory.workspace.workspace_indexer import (
    WorkspaceIndexer,
    WorkspaceIndexerConfig,
    WorkspaceFileEntry,
    WorkspaceIndex,
)
from memory.workspace.project_intelligence import (
    ProjectIntelligenceEngine,
    ProjectDetector,
    LanguageDetector,
    BuildSystemDetector,
    GitWorkspaceAnalyzer,
    WorkspaceAnalysis,
    GitSummary,
    BuildSystemSummary,
)
from memory.workspace.workspace_models import (
    WorkspaceError,
    InvalidWorkspaceError,
    WorkspaceNotFoundError,
    WORKSPACE_TEMPLATES,
)

__all__ = [
    "WorkspaceService",
    "WorkspaceManager",
    "WorkspaceValidator",
    "WorkspaceLauncher",
    "WorkspaceSnapshot",
    "WorkspaceDiscoveryEngine",
    "WorkspaceDiscoveryConfig",
    "WorkspaceDiscoveryResult",
    "WorkspaceIndexer",
    "WorkspaceIndexerConfig",
    "WorkspaceFileEntry",
    "WorkspaceIndex",
    "ProjectIntelligenceEngine",
    "ProjectDetector",
    "LanguageDetector",
    "BuildSystemDetector",
    "GitWorkspaceAnalyzer",
    "WorkspaceAnalysis",
    "GitSummary",
    "BuildSystemSummary",
    "WorkspaceError",
    "InvalidWorkspaceError",
    "WorkspaceNotFoundError",
    "WORKSPACE_TEMPLATES",
]
