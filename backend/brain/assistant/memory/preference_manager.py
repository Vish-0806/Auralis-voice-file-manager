"""Preference Manager implementation for Auralis (Phase 13.5).

Merges user, assistant, and runtime preferences with precedence validation and zero persistence logic.
Thread-safe using threading.RLock().
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, Optional

from brain.assistant.memory.exceptions import AssistantPreferenceError
from brain.assistant.memory.interfaces import IAssistantPreferenceManager
from brain.assistant.memory.models import AssistantMemoryScope, AssistantPreference

logger = logging.getLogger(__name__)


class PreferenceManager(IAssistantPreferenceManager):
    """Thread-safe manager for merging scoped preferences with deterministic override precedence."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()
        self._preferences: Dict[str, AssistantPreference] = {}

    def register_preference(self, preference: AssistantPreference) -> None:
        """Register an AssistantPreference model setting."""
        if not isinstance(preference, AssistantPreference) or not preference.key:
            raise AssistantPreferenceError("preference must be a valid AssistantPreference with non-empty key")

        with self._lock:
            self._preferences[preference.key] = preference
            logger.debug("Registered preference key='%s' scope=%s", preference.key, preference.scope)

    def get_preference(self, key: str) -> Optional[AssistantPreference]:
        """Retrieve a registered preference by key."""
        with self._lock:
            return self._preferences.get(key)

    def merge_preferences(
        self,
        user_prefs: Optional[Dict[str, Any]] = None,
        assistant_prefs: Optional[Dict[str, Any]] = None,
        runtime_prefs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Merge preferences with scope priority hierarchy: runtime < assistant < user."""
        with self._lock:
            merged: Dict[str, Any] = {}

            # 1. Registered preferences baseline
            for key, pref in self._preferences.items():
                merged[key] = pref.value

            # 2. Runtime Preferences (Lowest layer overrides)
            if runtime_prefs:
                merged.update(runtime_prefs)

            # 3. Assistant Preferences (Mid layer overrides)
            if assistant_prefs:
                merged.update(assistant_prefs)

            # 4. User Preferences (Highest layer overrides)
            if user_prefs:
                merged.update(user_prefs)

            logger.debug("Merged %d preference keys", len(merged))
            return merged

    def clear(self) -> None:
        """Clear registered preferences."""
        with self._lock:
            self._preferences.clear()
