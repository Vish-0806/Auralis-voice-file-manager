"""ContextManager coordinating ContextState, TemporaryMemory, and ReferenceResolver."""

from typing import Any, Dict, List, Optional
from utils.logger import get_logger

from voice.context.models import ContextState, ResolutionResult
from voice.context.memory import TemporaryMemory
from voice.context.reference_resolver import ReferenceResolver

logger = get_logger(__name__)


class ContextManager:
    """Manages active session context variables, temporary memory, and resolution calls."""

    def __init__(self) -> None:
        """Initializes the ContextManager with empty state, memory, and resolver."""
        self.state = ContextState()
        self.memory = TemporaryMemory()
        self.resolver = ReferenceResolver()

    def update(
        self,
        current_file: Optional[str] = None,
        current_folder: Optional[str] = None,
        current_search_results: Optional[List[str]] = None,
        current_capability: Optional[str] = None,
        last_intent: Optional[str] = None,
        last_execution_result: Optional[str] = None,
        pending_confirmation: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Updates active context state fields with new values.

        Args:
            current_file: File path or name.
            current_folder: Directory path or name.
            current_search_results: List of search outcomes.
            current_capability: Active capacity descriptor.
            last_intent: User intent classification.
            last_execution_result: Return output from last command run.
            pending_confirmation: Dict parameters for action confirmations.
        """
        logger.debug("Updating context state variables")
        if current_file is not None:
            self.state.current_file = current_file
        if current_folder is not None:
            self.state.current_folder = current_folder
        if current_search_results is not None:
            self.state.current_search_results = current_search_results
        if current_capability is not None:
            self.state.current_capability = current_capability
        if last_intent is not None:
            self.state.last_intent = last_intent
        if last_execution_result is not None:
            self.state.last_execution_result = last_execution_result
        if pending_confirmation is not None:
            self.state.pending_confirmation = pending_confirmation

    def resolve_references(self, command: str) -> ResolutionResult:
        """Resolves natural pronouns/nouns/ordinals in the input user string.

        Args:
            command: Plain text voice command.

        Returns:
            ResolutionResult enclosing the resolved string or clarification request.
        """
        logger.info("Resolving references in command: '%s'", command)
        return self.resolver.resolve(command, self.state)

    def clear(self) -> None:
        """Automatically resets context state fields and purges temporary memory."""
        logger.info("Clearing context manager state and purging temporary memory")
        self.state = ContextState()
        self.memory.clear()
