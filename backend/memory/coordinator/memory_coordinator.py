"""Unified Memory Coordinator module for Auralis."""

import logging
from typing import Any, Dict, List, Optional

from memory.preferences.preference_service import PreferenceService
from memory.context.context_service import ContextService
from memory.workspace.workspace_service import WorkspaceService
from memory.learning.routine_learning_service import RoutineLearningService
from memory.personalization.personalization_service import PersonalizationService

from memory.coordinator.memory_registry import MemoryRegistry
from memory.coordinator.memory_pipeline import MemoryPipeline
from memory.coordinator.memory_health import MemoryHealth

logger = logging.getLogger(__name__)


class MemoryCoordinator:
    """The unified single entry point for all memory platform operations in Auralis.

    The AI Brain and all external subsystems communicate exclusively through
    this coordinator, keeping individual memory services encapsulated.
    """

    def __init__(
        self,
        preference_service: Optional[PreferenceService] = None,
        context_service: Optional[ContextService] = None,
        workspace_service: Optional[WorkspaceService] = None,
        routine_service: Optional[RoutineLearningService] = None,
        personalization_service: Optional[PersonalizationService] = None,
        health_session_factory: Optional[Any] = None,
    ) -> None:
        """Initializes MemoryCoordinator and registers all memory services.

        Args:
            preference_service: Injected PreferenceService.
            context_service: Injected ContextService.
            workspace_service: Injected WorkspaceService.
            routine_service: Injected RoutineLearningService.
            personalization_service: Injected PersonalizationService.
            health_session_factory: Optional custom health check session creator.
        """
        # Resolve services
        self.preferences = preference_service or PreferenceService()
        self.context = context_service or ContextService()
        self.workspace = workspace_service or WorkspaceService()
        self.learning = routine_service or RoutineLearningService()
        self.personalization = personalization_service or PersonalizationService(
            preference_service=self.preferences,
            context_service=self.context,
            workspace_service=self.workspace,
            routine_service=self.learning,
        )

        # Register in MemoryRegistry
        MemoryRegistry.clear()
        MemoryRegistry.register("preferences", self.preferences)
        MemoryRegistry.register("context", self.context)
        MemoryRegistry.register("workspace", self.workspace)
        MemoryRegistry.register("learning", self.learning)
        MemoryRegistry.register("personalization", self.personalization)

        # Setup sub-components
        self._pipeline = MemoryPipeline(self.personalization)
        self._health = MemoryHealth(MemoryRegistry, session_factory=health_session_factory)

    # 1. Preferences Delegation Interface
    def get_preference(self, user_id: int, category: str, key: Optional[str] = None) -> Any:
        """Loads preference configurations. If key is None, lists all in category."""
        if key is not None:
            return self.preferences.get(user_id, category, key)
        return self.preferences.list(user_id, category)

    def set_preference(self, user_id: int, category: str, setting_key: str, value: Any) -> Any:
        """Sets and validates a user preference value."""
        return self.preferences.set(user_id, category, setting_key, value)

    def reset_preferences(self, user_id: int, category: Optional[str] = None) -> None:
        """Resets configurations to templates default mapping."""
        self.preferences.reset(user_id, category)

    # 2. Context Delegation Interface
    def save_context(
        self, user_id: int, session_id: str, context_type: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> Any:
        """Saves and validates execution context."""
        return self.context.save(user_id, session_id, context_type, value, ttl_seconds)

    def load_context(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Loads non-expired active context mappings."""
        return self.context.load(user_id, session_id)

    def delete_context(self, user_id: int, session_id: str, context_type: Optional[str] = None) -> bool:
        """Deletes session context settings."""
        return self.context.delete(user_id, session_id, context_type)

    def restore_context(self, user_id: int, session_id: str, metadata_bag: Dict[str, Any]) -> Any:
        """Restores context parameters bag."""
        return self.context.restore(user_id, session_id, metadata_bag)

    # 3. Workspace Delegation Interface
    def create_workspace(self, user_id: int, name: str, path: str, settings: Dict[str, Any]) -> Any:
        """Creates a workspace profile setup."""
        return self.workspace.create(user_id, name, path, settings)

    def get_workspace(self, user_id: int, profile_id: int) -> Any:
        """Gets a workspace profile by ID."""
        return self.workspace.get(user_id, profile_id)

    def list_workspaces(self, user_id: int) -> List[Any]:
        """Lists user workspace profiles."""
        return self.workspace.list(user_id)

    def restore_workspace(self, user_id: int, profile_id: int) -> bool:
        """Executes profile launches routing to OS capability."""
        return self.workspace.restore(user_id, profile_id)

    def snapshot_workspace(self, user_id: int, session_id: str, profile_name: str) -> Any:
        """Captures disk path and window owner list to save profile."""
        return self.workspace.snapshot(user_id, session_id, profile_name, self.context)

    # 4. Learning Delegation Interface
    def record_execution(
        self, user_id: int, action: str, input_parameters: Dict[str, Any], status: str, duration_ms: Optional[int] = None
    ) -> Any:
        """Records an execution outcome event log."""
        return self.learning.record(user_id, action, input_parameters, status, duration_ms)

    def analyze_learning(self, user_id: int) -> List[Any]:
        """Mines executions history for repeating suggestions."""
        return self.learning.analyze(user_id)

    def accept_routine(self, user_id: int, suggestion: Any) -> Any:
        """Confirms routine suggestion, saving it to active routines."""
        return self.learning.accept(user_id, suggestion)

    def reject_routine(self, user_id: int, trigger_event: str) -> None:
        """Mutes suggested trigger event from future suggestions."""
        self.learning.reject(user_id, trigger_event)

    def list_routines(self, user_id: int) -> List[Any]:
        """Lists active routines."""
        return self.learning.list(user_id)

    # 5. Personalization Delegation Interface
    def get_profile(self, user_id: int, session_id: str) -> Any:
        """Aggregates memory states to build a UserProfile summary."""
        return self.personalization.profile(user_id, session_id)

    def get_recommendations(self, user_id: int, session_id: str) -> List[Any]:
        """Runs behaviour check calculations to return suggestions list."""
        return self.personalization.recommendations(user_id, session_id)

    # 6. Pipeline & Health operations
    def run_pipeline(
        self, user_id: int, session_id: str, user_overrides: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Runs the context resolution pipeline sequentially."""
        return self._pipeline.process(user_id, session_id, user_overrides)

    def check_health(self) -> Dict[str, Any]:
        """Runs system connection and registry diagnostics."""
        return self._health.check_health()

    def get_metrics(self, user_id: int) -> Dict[str, Any]:
        """Compiles diagnostics statistics counts."""
        return self._health.get_metrics(user_id)
