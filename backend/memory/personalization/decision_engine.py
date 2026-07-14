"""Personalization conflict resolution and decision engine."""

import logging
from typing import Any, Dict, List, Optional
from memory.personalization.personalization_models import PersonalizedContext

logger = logging.getLogger(__name__)

SYSTEM_DEFAULTS: Dict[str, Any] = {
    "theme": "dark",
    "editor": "VS Code",
    "shell": "powershell",
    "voice_provider": "google",
    "speech_rate": 150,
    "workspace_path": "/workspace",
}


class DecisionEngine:
    """Resolves conflicts between different user memory sources using strict deterministic priorities."""

    @staticmethod
    def resolve_setting(
        key: str,
        user_overrides: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        workspace_settings: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        learned_routines: Optional[List[Any]] = None,
    ) -> tuple[Any, str]:
        """Resolves the value of a specific setting key by stepping down the priority ladder.

        Priority Order:
        1. Explicit User Command (user_overrides)
        2. Current Context
        3. Workspace Profile settings
        4. User Preferences
        5. Learned Routine
        6. System Defaults

        Args:
            key: Config setting key.
            user_overrides: Overrides passed in request.
            context: Context memory values.
            workspace_settings: Active workspace settings.
            preferences: User preferences dict.
            learned_routines: List of learned active routines.

        Returns:
            Tuple of (resolved_value, source_name).
        """
        # Priority 1: Explicit User Command
        if user_overrides and key in user_overrides:
            return user_overrides[key], "Explicit User Command"

        # Priority 2: Current Context
        if context and key in context:
            return context[key], "Current Context"

        # Priority 3: Workspace Profile settings
        if workspace_settings:
            # Check direct or environmental keys
            if key in workspace_settings:
                return workspace_settings[key], "Workspace Profile"
            # Env var backup checks
            env_vars = workspace_settings.get("env_vars", {})
            if key.upper() in env_vars:
                return env_vars[key.upper()], "Workspace Profile"

        # Priority 4: User Preferences
        if preferences:
            # Check raw category-nested pref settings (flat-mapped)
            for category, settings in preferences.items():
                if isinstance(settings, dict) and key in settings:
                    return settings[key], "User Preferences"

        # Priority 5: Learned Routine
        if learned_routines:
            for routine in learned_routines:
                # E.g. check trigger or action steps to match editor/shell
                steps = routine.action_sequence.get("steps", []) if hasattr(routine, "action_sequence") else []
                for step in steps:
                    action = step.get("action", "")
                    if action == "OPEN_APPLICATION" and key == "editor":
                        target = step.get("input_parameters", {}).get("target", "")
                        if target in ["VS Code", "Notepad", "Cursor"]:
                            return target, "Learned Routine"

        # Priority 6: System Defaults
        return SYSTEM_DEFAULTS.get(key), "System Defaults"

    @classmethod
    def generate_context(
        cls,
        user_id: int,
        session_id: str,
        user_overrides: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        workspace_settings: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        learned_routines: Optional[List[Any]] = None,
    ) -> PersonalizedContext:
        """Generates a complete PersonalizedContext resolving all standard settings keys.

        Args:
            user_id: Owner user ID.
            session_id: Active session ID.
            user_overrides: Explicit overrides in request.
            context: Active Context parameters.
            workspace_settings: Active Workspace settings.
            preferences: User preferences.
            learned_routines: User routines.

        Returns:
            The generated PersonalizedContext.
        """
        logger.info(f"Generating personalized context for user {user_id} (session: {session_id}).")

        resolved_settings = {}
        source_mapping = {}

        for key in SYSTEM_DEFAULTS:
            val, src = cls.resolve_setting(
                key=key,
                user_overrides=user_overrides,
                context=context,
                workspace_settings=workspace_settings,
                preferences=preferences,
                learned_routines=learned_routines,
            )
            resolved_settings[key] = val
            source_mapping[key] = src

        return PersonalizedContext(
            user_id=user_id,
            session_id=session_id,
            resolved_settings=resolved_settings,
            source_mapping=source_mapping,
        )
