"""WorkspaceContext component for building and injecting workspace metadata into prompts (Phase 10.3).

Injects current directory, selected files, operating system, active workspace,
and environment metadata into prompts using mock providers without filesystem I/O.
"""

import logging
import platform
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from brain.ai.ai_models import AIContext, PromptMessage, PromptRole
from brain.ai.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class WorkspaceContextProviderInterface(ABC):
    """Abstract interface for workspace context metadata providers."""

    @abstractmethod
    def get_workspace_metadata(self, context: AIContext) -> Dict[str, Any]:
        """Fetch workspace metadata dictionary for a given AIContext."""
        pass


class MockWorkspaceContextProvider(WorkspaceContextProviderInterface):
    """Mock workspace provider delivering configurable workspace metadata without filesystem calls."""

    def __init__(
        self,
        default_dir: str = "/workspace",
        default_active_workspace: str = "Auralis-voice-file-manager",
        default_selected_files: Optional[List[str]] = None,
        default_env_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.default_dir = default_dir
        self.default_active_workspace = default_active_workspace
        self.default_selected_files = default_selected_files or []
        self.default_env_metadata = default_env_metadata or {"mode": "development", "python_version": platform.python_version()}

    def get_workspace_metadata(self, context: AIContext) -> Dict[str, Any]:
        ws = context.workspace_context if context.workspace_context else {}

        return {
            "current_dir": ws.get("current_dir", ws.get("root", self.default_dir)),
            "active_workspace": ws.get("active_workspace", ws.get("name", self.default_active_workspace)),
            "operating_system": ws.get("operating_system", ws.get("os", platform.system())),
            "selected_files": ws.get("selected_files", self.default_selected_files),
            "env_metadata": ws.get("env_metadata", ws.get("env", self.default_env_metadata)),
        }


class WorkspaceContextInjector:
    """Injects workspace context into prompt text and PromptMessage objects."""

    def __init__(
        self,
        workspace_provider: Optional[WorkspaceContextProviderInterface] = None,
        templates: Optional[PromptTemplates] = None,
    ) -> None:
        self.workspace_provider = workspace_provider or MockWorkspaceContextProvider()
        self.templates = templates or PromptTemplates()

    def inject_workspace(
        self,
        context: AIContext,
        provider_override: Optional[WorkspaceContextProviderInterface] = None,
    ) -> str:
        """Extract workspace metadata and render workspace prompt string.

        Args:
            context: Constructed AIContext object.
            provider_override: Optional provider instance override.

        Returns:
            Formatted workspace prompt text string.
        """
        try:
            provider = provider_override or self.workspace_provider
            ws_data = provider.get_workspace_metadata(context)

            return self.templates.render_workspace(
                current_dir=ws_data.get("current_dir", "None"),
                active_workspace=ws_data.get("active_workspace", "None"),
                operating_system=ws_data.get("operating_system", "Unknown"),
                selected_files=ws_data.get("selected_files", "None"),
                env_metadata=ws_data.get("env_metadata", "None"),
            )
        except Exception as exc:
            logger.warning(f"Failed to inject workspace context: {exc}")
            return "Workspace Context: None"

    def build_workspace_message(
        self,
        context: AIContext,
        provider_override: Optional[WorkspaceContextProviderInterface] = None,
    ) -> Optional[PromptMessage]:
        """Construct a PromptMessage with WORKSPACE role containing formatted workspace context."""
        text = self.inject_workspace(context, provider_override=provider_override)
        if not text or text.strip() == "Workspace Context: None":
            return None

        return PromptMessage(role=PromptRole.WORKSPACE, content=text)
