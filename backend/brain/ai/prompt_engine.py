"""PromptEngine / PromptBuilder implementation (Phase 10.1 & Phase 10.3).

Assembles system, developer, memory, workspace, conversation, tool, and user prompts
using PromptTemplates, MemoryInjector, WorkspaceContextInjector, ConversationBuilder,
TokenEstimator, and PromptOptimizer services.
"""

from typing import List, Optional

from brain.ai.exceptions import PromptBuildError
from brain.ai.interfaces import PromptBuilder
from brain.ai.ai_models import AIContext, Prompt, PromptMessage, PromptRole
from brain.ai.prompt_templates import PromptTemplates
from brain.ai.token_estimator import TokenEstimator
from brain.ai.conversation_builder import ConversationBuilder
from brain.ai.memory_injector import MemoryInjector
from brain.ai.workspace_context import WorkspaceContextInjector
from brain.ai.prompt_optimizer import PromptOptimizer


class DefaultPromptBuilder(PromptBuilder):
    """Default implementation of PromptBuilder interface with full prompt intelligence pipeline."""

    def __init__(
        self,
        base_system_prompt: str = "You are Auralis, an intelligent voice and file management AI assistant.",
        templates: Optional[PromptTemplates] = None,
        token_estimator: Optional[TokenEstimator] = None,
        conversation_builder: Optional[ConversationBuilder] = None,
        memory_injector: Optional[MemoryInjector] = None,
        workspace_injector: Optional[WorkspaceContextInjector] = None,
        prompt_optimizer: Optional[PromptOptimizer] = None,
    ) -> None:
        self.base_system_prompt = base_system_prompt
        self.templates = templates or PromptTemplates(system_template=base_system_prompt)
        self.token_estimator = token_estimator or TokenEstimator()
        self.conversation_builder = conversation_builder or ConversationBuilder(token_estimator=self.token_estimator)
        self.memory_injector = memory_injector or MemoryInjector(templates=self.templates)
        self.workspace_injector = workspace_injector or WorkspaceContextInjector(templates=self.templates)
        self.prompt_optimizer = prompt_optimizer or PromptOptimizer(token_estimator=self.token_estimator)

    def build_prompt(self, context: AIContext, max_tokens: Optional[int] = None) -> Prompt:
        """Build and optimize a structured Prompt instance from AIContext.

        Args:
            context: Constructed AIContext object.
            max_tokens: Optional token limit cap.

        Returns:
            Optimized Prompt model with formatted messages and token estimates.

        Raises:
            PromptBuildError: If prompt generation or optimization encounters an error.
        """
        try:
            # 1. Render system & developer prompt strings
            system_prompt = self.templates.render_system(assistant_name="Auralis")
            developer_prompt = self.templates.render_developer()

            # 2. Inject memory & workspace context strings
            memory_prompt = self.memory_injector.inject_memory(context)
            workspace_prompt = self.workspace_injector.inject_workspace(context)

            # 3. Format conversation history into PromptMessage list
            history_messages = self.conversation_builder.build_conversation(context.conversation_history)

            # 4. User & Tool prompts
            user_prompt = context.raw_query
            tool_prompt = "Available tools: filesystem, memory, automation, voice, planner, execution."

            # 5. Assemble formatted messages
            messages: List[PromptMessage] = [
                PromptMessage(role=PromptRole.SYSTEM, content=system_prompt),
                PromptMessage(role=PromptRole.DEVELOPER, content=developer_prompt),
            ]

            if memory_prompt and memory_prompt != "Memory Context: None":
                messages.append(PromptMessage(role=PromptRole.MEMORY, content=memory_prompt))

            if workspace_prompt and workspace_prompt != "Workspace Context: None":
                messages.append(PromptMessage(role=PromptRole.WORKSPACE, content=workspace_prompt))

            if history_messages:
                messages.extend(history_messages)

            if tool_prompt:
                messages.append(PromptMessage(role=PromptRole.TOOL, content=tool_prompt))

            if user_prompt:
                messages.append(PromptMessage(role=PromptRole.USER, content=user_prompt))

            # 6. Construct initial Prompt object
            raw_prompt = Prompt(
                system_prompt=system_prompt,
                developer_prompt=developer_prompt,
                user_prompt=user_prompt,
                tool_prompt=tool_prompt,
                memory_prompt=memory_prompt,
                workspace_prompt=workspace_prompt,
                formatted_messages=messages,
                token_estimate=self.token_estimator.estimate_tokens(messages),
                metadata={"builder": "DefaultPromptBuilder", "context_id": context.request_id},
            )

            # 7. Optimize prompt (deduplicate, sort by priority order, trim if max_tokens set)
            return self.prompt_optimizer.optimize_prompt(raw_prompt, max_tokens=max_tokens)

        except Exception as exc:
            raise PromptBuildError(f"Failed to build Prompt: {exc}") from exc
