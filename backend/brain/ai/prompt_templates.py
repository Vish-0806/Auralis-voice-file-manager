"""Reusable Prompt Templates and template engine for Auralis (Phase 10.3).

Provides configurable templates for System, Developer, Memory, and Workspace prompts.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_TEMPLATE = (
    "You are {assistant_name}, an intelligent voice and file management AI assistant."
)

DEFAULT_DEVELOPER_TEMPLATE = (
    "Maintain safety, precision, and user privacy at all times. "
    "Adhere to system instructions and verify actions before execution."
)

DEFAULT_MEMORY_TEMPLATE = (
    "Memory Context:\n"
    "- Long-Term Memory: {long_term}\n"
    "- Recent Memory: {recent}\n"
    "- User Preferences: {preferences}\n"
    "- Pinned Memory: {pinned}\n"
    "- Execution State: {execution}"
)

DEFAULT_WORKSPACE_TEMPLATE = (
    "Workspace Context:\n"
    "- Current Working Directory: {current_dir}\n"
    "- Active Workspace: {active_workspace}\n"
    "- Operating System: {operating_system}\n"
    "- Selected Files: {selected_files}\n"
    "- Environment Metadata: {env_metadata}"
)


class PromptTemplates:
    """Configurable and reusable prompt template engine."""

    def __init__(
        self,
        system_template: str = DEFAULT_SYSTEM_TEMPLATE,
        developer_template: str = DEFAULT_DEVELOPER_TEMPLATE,
        memory_template: str = DEFAULT_MEMORY_TEMPLATE,
        workspace_template: str = DEFAULT_WORKSPACE_TEMPLATE,
    ) -> None:
        self.system_template = system_template
        self.developer_template = developer_template
        self.memory_template = memory_template
        self.workspace_template = workspace_template

    def render_system(self, assistant_name: str = "Auralis", **kwargs: Any) -> str:
        """Render the system prompt with given parameters."""
        try:
            return self.system_template.format(assistant_name=assistant_name, **kwargs)
        except Exception as exc:
            logger.warning(f"Error rendering system template: {exc}. Fallback used.")
            return f"You are {assistant_name}, an intelligent assistant."

    def render_developer(self, **kwargs: Any) -> str:
        """Render the developer prompt with given parameters."""
        try:
            return self.developer_template.format(**kwargs)
        except Exception as exc:
            logger.warning(f"Error rendering developer template: {exc}. Fallback used.")
            return self.developer_template

    def render_memory(
        self,
        long_term: Any = "None",
        recent: Any = "None",
        preferences: Any = "None",
        pinned: Any = "None",
        execution: Any = "None",
        **kwargs: Any,
    ) -> str:
        """Render the memory prompt with memory parameters."""
        try:
            return self.memory_template.format(
                long_term=long_term,
                recent=recent,
                preferences=preferences,
                pinned=pinned,
                execution=execution,
                **kwargs,
            )
        except Exception as exc:
            logger.warning(f"Error rendering memory template: {exc}. Fallback used.")
            return f"Memory Context: long_term={long_term}, recent={recent}, preferences={preferences}"

    def render_workspace(
        self,
        current_dir: Any = "None",
        active_workspace: Any = "None",
        operating_system: Any = "Unknown",
        selected_files: Any = "None",
        env_metadata: Any = "None",
        **kwargs: Any,
    ) -> str:
        """Render the workspace prompt with workspace parameters."""
        try:
            return self.workspace_template.format(
                current_dir=current_dir,
                active_workspace=active_workspace,
                operating_system=operating_system,
                selected_files=selected_files,
                env_metadata=env_metadata,
                **kwargs,
            )
        except Exception as exc:
            logger.warning(f"Error rendering workspace template: {exc}. Fallback used.")
            return f"Workspace Context: dir={current_dir}, os={operating_system}"
