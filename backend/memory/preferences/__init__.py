"""Unified entry point for the User Preference Engine and learning subsystem."""

from memory.preferences.preference_service import PreferenceService
from memory.preferences.preference_engine import PreferenceEngine
from memory.preferences.preference_validator import PreferenceValidator
from memory.preferences.preference_cache import PreferenceCache
from memory.preferences.preference_models import (
    PreferenceError,
    InvalidPreferenceError,
    DuplicatePreferenceError,
    VALID_PREFERENCES,
)

# New Preference Learning imports
from memory.preferences.preference_learning import (
    PreferenceObservation,
    PreferenceCandidate,
    ResolvedPreference,
    PreferenceStatistics,
    PreferenceScorer,
    PreferenceLearner,
    PreferenceConflictResolver,
    PreferenceLearningCoordinator,
    PreferenceResolver,
    ensure_utc,
)

__all__ = [
    # Legacy User Preference Engine
    "PreferenceService",
    "PreferenceEngine",
    "PreferenceValidator",
    "PreferenceCache",
    "PreferenceError",
    "InvalidPreferenceError",
    "DuplicatePreferenceError",
    "VALID_PREFERENCES",
    
    # New Preference Learning
    "PreferenceObservation",
    "PreferenceCandidate",
    "ResolvedPreference",
    "PreferenceStatistics",
    "PreferenceScorer",
    "PreferenceLearner",
    "PreferenceConflictResolver",
    "PreferenceLearningCoordinator",
    "PreferenceResolver",
    "ensure_utc",
]
