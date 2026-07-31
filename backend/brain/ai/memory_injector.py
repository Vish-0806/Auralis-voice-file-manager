"""MemoryInjector component for assembling and injecting memory context into prompts (Phase 10.3).

Extracts and injects long-term memory, recent memory, user preferences, pinned memory,
and execution context from AIContext. Uses dependency injection without database access.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from brain.ai.ai_models import AIContext, PromptMessage, PromptRole
from brain.ai.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class MemoryProviderInterface(ABC):
    """Abstract interface for external memory providers."""

    @abstractmethod
    def fetch_memory(self, context: AIContext) -> Dict[str, Any]:
        """Fetch memory facets dictionary for a given AIContext."""
        pass


class DefaultMemoryProvider(MemoryProviderInterface):
    """Default memory provider extracting memory fields directly from AIContext."""

    def fetch_memory(self, context: AIContext) -> Dict[str, Any]:
        raw_memory = context.memory_context if context.memory_context else {}
        exec_ctx = context.execution_context if context.execution_context else {}

        long_term = raw_memory.get("long_term", "None")
        recent = raw_memory.get("recent", "None")
        preferences = raw_memory.get("preferences", raw_memory.get("user_preferences", "None"))
        pinned = raw_memory.get("pinned", "None")

        if preferences == "None" and raw_memory:
            preferences = str(raw_memory)

        return {
            "long_term": long_term,
            "recent": recent,
            "preferences": preferences,
            "pinned": pinned,
            "execution": exec_ctx.get("state", raw_memory.get("execution", "None")),
        }


class MemoryInjector:
    """Injects memory context facets into prompt text and PromptMessage objects."""

    def __init__(
        self,
        memory_provider: Optional[MemoryProviderInterface] = None,
        templates: Optional[PromptTemplates] = None,
    ) -> None:
        self.memory_provider = memory_provider or DefaultMemoryProvider()
        self.templates = templates or PromptTemplates()

    def inject_memory(self, context: AIContext, custom_template: Optional[str] = None) -> str:
        """Extract memory facets from context and format memory prompt text.

        Args:
            context: Constructed AIContext object.
            custom_template: Optional custom template string override.

        Returns:
            Formatted memory context prompt text string.
        """
        try:
            mem_data = self.memory_provider.fetch_memory(context)

            if custom_template:
                return custom_template.format(**mem_data)

            return self.templates.render_memory(
                long_term=mem_data.get("long_term", "None"),
                recent=mem_data.get("recent", "None"),
                preferences=mem_data.get("preferences", "None"),
                pinned=mem_data.get("pinned", "None"),
                execution=mem_data.get("execution", "None"),
            )
        except Exception as exc:
            logger.warning(f"Failed to inject memory context: {exc}")
            return "Memory Context: None"

    def build_memory_message(self, context: AIContext) -> Optional[PromptMessage]:
        """Construct a PromptMessage with MEMORY role containing formatted memory context."""
        text = self.inject_memory(context)
        if not text or text.strip() == "Memory Context: None":
            return None

        return PromptMessage(role=PromptRole.MEMORY, content=text)
