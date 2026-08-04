"""Comprehensive unit tests for Phase 14.3.4 Configuration Profiles & Feature Flag Runtime."""

from datetime import timedelta
from enum import Enum
import concurrent.futures
import os
from pathlib import Path
import tempfile
from typing import Tuple
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.configuration_resolver import ConfigurationResolver
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.configuration_schema import ConfigurationSchemaManager
from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.configuration_validator import ConfigurationValidator
from backend.application.config.dotenv_source import DotEnvConfigurationSource
from backend.application.config.environment_source import EnvironmentConfigurationSource
from backend.application.config.exceptions import (
    ConfigurationException,
    ConfigurationInitializationError,
    ConfigurationProfileError,
    ConfigurationProviderError,
    ConfigurationSourceError,
    ConfigurationValidationError,
)
from backend.application.config.feature_flag_manager import FeatureFlagManager
from backend.application.config.interfaces import (
    IConfigurationDiagnostics,
    IConfigurationManager,
    IConfigurationProvider,
    IConfigurationRuntime,
    IConfigurationSource,
    IConfigurationValidator,
)
from backend.application.config.memory_source import MemoryConfigurationSource
from backend.application.config.models import (
    ConfigurationCapabilities,
    ConfigurationConstraint,
    ConfigurationContext,
    ConfigurationDefinition,
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationError,
    ConfigurationHealth,
    ConfigurationProfile,
    ConfigurationProfileDefinition,
    ConfigurationProfileSnapshot,
    ConfigurationProfileType,
    ConfigurationResolutionResult,
    ConfigurationRuntimeState,
    ConfigurationSchema,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationSourceType,
    ConfigurationState,
    ConfigurationStatistics,
    ConfigurationValidationResult,
    ConfigurationWarning,
    FeatureEvaluation,
    FeatureFlag,
    FeatureHealth,
    FeatureStatistics,
    ProfileHealth,
    ProfileStatistics,
    ResolutionStatistics,
    SourceHealth,
    SourcePriority,
    SourceRegistration,
    SourceStatistics,
    ValidationStatistics,
)
from backend.application.config.profile_manager import ProfileManager
from backend.application.config.runtime import (
    get_configuration_provider,
    get_configuration_runtime,
    reset_configuration_provider,
    reset_configuration_runtime,
    set_configuration_provider,
    set_configuration_runtime,
)
from backend.application.config.source_registry import SourceRegistry


class SampleEnvEnum(str, Enum):
    """Sample enum for testing conversion."""
    LOCAL = "local"
    PROD = "prod"


# ============================================================================
# 1. Models & Enum Tests
# ============================================================================


def test_configuration_runtime_state_enum():
    """Verify ConfigurationRuntimeState enum values."""
    assert ConfigurationRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ConfigurationRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert ConfigurationRuntimeState.READY.value == "READY"
    assert ConfigurationRuntimeState.STOPPING.value == "STOPPING"
    assert ConfigurationRuntimeState.STOPPED.value == "STOPPED"


def test_configuration_source_type_enum():
    """Verify ConfigurationSourceType enum values."""
    assert ConfigurationSourceType.ENVIRONMENT.value == "ENVIRONMENT"
    assert ConfigurationSourceType.DOTENV.value == "DOTENV"
    assert ConfigurationSourceType.JSON.value == "JSON"
    assert ConfigurationSourceType.YAML.value == "YAML"
    assert ConfigurationSourceType.MEMORY.value == "MEMORY"
    assert ConfigurationSourceType.REMOTE.value == "REMOTE"


def test_configuration_profile_type_enum():
    """Verify ConfigurationProfileType enum values."""
    assert ConfigurationProfileType.DEVELOPMENT.value == "DEVELOPMENT"
    assert ConfigurationProfileType.TESTING.value == "TESTING"
    assert ConfigurationProfileType.STAGING.value == "STAGING"
    assert ConfigurationProfileType.PRODUCTION.value == "PRODUCTION"


def test_source_priority_enum_values():
    """Verify SourcePriority integer levels."""
    assert SourcePriority.MEMORY == 500
    assert SourcePriority.ENVIRONMENT == 400
    assert SourcePriority.DOTENV == 300
    assert SourcePriority.JSON == 200
    assert SourcePriority.YAML == 100
    assert SourcePriority.REMOTE == 50
    assert SourcePriority.DEFAULT == 0


def test_feature_flag_model_immutability():
    """Verify FeatureFlag Pydantic v2 model attributes and immutability."""
    flag = FeatureFlag(feature_name="beta_ui", enabled=True, rollout_percentage=50.0)
    assert flag.feature_name == "beta_ui"
    assert flag.rollout_percentage == 50.0

    with pytest.raises(ValidationError):
        flag.enabled = False  # type: ignore[misc]


def test_feature_evaluation_model_fields():
    """Verify FeatureEvaluation model fields."""
    eval_res = FeatureEvaluation(feature_name="beta_ui", enabled=True, reason="Active")
    assert eval_res.feature_name == "beta_ui"
    assert eval_res.enabled is True
    assert eval_res.reason == "Active"


def test_profile_definition_and_snapshot_models():
    """Verify ConfigurationProfileDefinition and ConfigurationProfileSnapshot models."""
    p_def = ConfigurationProfileDefinition(profile_name="custom", overrides={"theme": "dark"})
    p_snap = ConfigurationProfileSnapshot(active_profile_name="custom", merged_values={"theme": "dark"})

    assert p_def.profile_name == "custom"
    assert p_snap.merged_values["theme"] == "dark"


def test_profile_health_and_statistics_models():
    """Verify ProfileHealth and ProfileStatistics models."""
    p_health = ProfileHealth(is_healthy=True, active_profile_name="dev")
    p_stats = ProfileStatistics(registered_profiles_count=3)

    assert p_health.is_healthy is True
    assert p_stats.registered_profiles_count == 3


def test_feature_health_and_statistics_models():
    """Verify FeatureHealth and FeatureStatistics models."""
    f_health = FeatureHealth(is_healthy=True)
    f_stats = FeatureStatistics(total_features=5, enabled_features=4)

    assert f_health.is_healthy is True
    assert f_stats.total_features == 5


# ============================================================================
# 2. Profile Manager Tests (Phase 14.3.4)
# ============================================================================


def test_profile_manager_register_and_list_profiles():
    """Verify ProfileManager profile registration and listing."""
    manager = ProfileManager()
    custom_p = ConfigurationProfileDefinition(profile_name="custom_profile", overrides={"custom_key": "val"})

    assert manager.register_profile(custom_p) is True
    profiles = manager.list_profiles()
    assert any(p.profile_name == "custom_profile" for p in profiles)


def test_profile_manager_duplicate_profile_raises():
    """Verify registering duplicate profile_name raises ConfigurationProfileError."""
    manager = ProfileManager()
    p1 = ConfigurationProfileDefinition(profile_name="dup")
    p2 = ConfigurationProfileDefinition(profile_name="dup")

    manager.register_profile(p1)
    with pytest.raises(ConfigurationProfileError):
        manager.register_profile(p2)


def test_profile_manager_activate_profile():
    """Verify activate_profile switches active profile safely."""
    manager = ProfileManager()
    assert manager.get_active_profile().profile_name == "development"

    assert manager.activate_profile("testing") is True
    assert manager.get_active_profile().profile_name == "testing"


def test_profile_manager_activate_unregistered_profile_raises():
    """Verify activating unregistered profile raises ConfigurationProfileError."""
    manager = ProfileManager()
    with pytest.raises(ConfigurationProfileError):
        manager.activate_profile("non_existent_profile")


def test_profile_manager_unregister_profile():
    """Verify unregistering inactive profile."""
    manager = ProfileManager()
    p = ConfigurationProfileDefinition(profile_name="temp_p")
    manager.register_profile(p)

    assert manager.unregister_profile("temp_p") is True
    assert not any(pr.profile_name == "temp_p" for pr in manager.list_profiles())


def test_profile_manager_unregister_active_profile_raises():
    """Verify unregistering active profile raises ConfigurationProfileError."""
    manager = ProfileManager()
    with pytest.raises(ConfigurationProfileError):
        manager.unregister_profile("development")


def test_profile_manager_inheritance_chain_resolution():
    """Verify profile inheritance chain resolution (parent -> child overrides)."""
    manager = ProfileManager()
    parent_p = ConfigurationProfileDefinition(profile_name="parent", overrides={"a": 1, "b": 2})
    child_p = ConfigurationProfileDefinition(profile_name="child", parent_profile_name="parent", overrides={"b": 99, "c": 3})

    manager.register_profile(parent_p)
    manager.register_profile(child_p)

    merged = manager.resolve_profile("child")
    assert merged["a"] == 1
    assert merged["b"] == 99  # Child overrides parent
    assert merged["c"] == 3


def test_profile_manager_circular_inheritance_raises():
    """Verify circular inheritance raises ConfigurationProfileError."""
    manager = ProfileManager()
    p1 = ConfigurationProfileDefinition(profile_name="circ1", parent_profile_name="circ2")
    p2 = ConfigurationProfileDefinition(profile_name="circ2", parent_profile_name="circ1")

    manager.register_profile(p1)
    manager.register_profile(p2)

    with pytest.raises(ConfigurationProfileError):
        manager.resolve_profile("circ1")


def test_profile_manager_create_snapshot():
    """Verify create_snapshot generation."""
    manager = ProfileManager()
    snapshot = manager.create_snapshot()

    assert isinstance(snapshot, ConfigurationProfileSnapshot)
    assert snapshot.active_profile_name == "development"
    assert "debug" in snapshot.merged_values


def test_profile_manager_health_and_statistics():
    """Verify ProfileManager health and statistics."""
    manager = ProfileManager()
    assert manager.health().is_healthy is True
    assert manager.statistics().registered_profiles_count >= 3


# ============================================================================
# 3. Feature Flag Manager Tests (Phase 14.3.4)
# ============================================================================


def test_feature_flag_manager_register_and_list_features():
    """Verify FeatureFlagManager feature registration and listing."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="feat_a", enabled=True)

    assert manager.register_feature(flag) is True
    features = manager.list_features()
    assert any(f.feature_name == "feat_a" for f in features)


def test_feature_flag_manager_remove_feature():
    """Verify removing registered feature flag."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="temp_feat")
    manager.register_feature(flag)

    assert manager.remove_feature("temp_feat") is True
    assert manager.remove_feature("missing_feat") is False


def test_feature_flag_manager_enable_disable_toggle():
    """Verify enabling, disabling, and toggling features."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="toggle_feat", enabled=False)
    manager.register_feature(flag)

    assert manager.is_enabled("toggle_feat") is False
    assert manager.enable("toggle_feat") is True
    assert manager.is_enabled("toggle_feat") is True

    assert manager.disable("toggle_feat") is True
    assert manager.is_enabled("toggle_feat") is False

    new_state = manager.toggle("toggle_feat")
    assert new_state is True


def test_feature_flag_manager_evaluate_basic():
    """Verify basic feature flag evaluation."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="basic_feat", enabled=True)
    manager.register_feature(flag)

    eval_res = manager.evaluate("basic_feat")
    assert eval_res.enabled is True
    assert eval_res.feature_name == "basic_feat"


def test_feature_flag_manager_evaluate_missing_feature():
    """Verify missing feature flag returns disabled evaluation."""
    manager = FeatureFlagManager()
    eval_res = manager.evaluate("missing_feat")
    assert eval_res.enabled is False
    assert "not registered" in eval_res.reason


def test_feature_flag_manager_evaluate_dependencies():
    """Verify dependency feature flag evaluation chain."""
    manager = FeatureFlagManager()
    parent_flag = FeatureFlag(feature_name="parent_feat", enabled=False)
    child_flag = FeatureFlag(feature_name="child_feat", enabled=True, dependencies=("parent_feat",))

    manager.register_feature(parent_flag)
    manager.register_feature(child_flag)

    # Child feature disabled because parent feature is disabled
    assert manager.is_enabled("child_feat") is False

    # Enable parent feature -> child feature becomes enabled
    manager.enable("parent_feat")
    assert manager.is_enabled("child_feat") is True


def test_feature_flag_manager_evaluate_allowed_profiles():
    """Verify profile restriction evaluation."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(
        feature_name="prod_only_feat",
        enabled=True,
        allowed_profiles=(ConfigurationProfileType.PRODUCTION,),
    )
    manager.register_feature(flag)

    assert manager.evaluate("prod_only_feat", active_profile_name="development").enabled is False
    assert manager.evaluate("prod_only_feat", active_profile_name="production").enabled is True


def test_feature_flag_manager_evaluate_allowed_environments():
    """Verify environment restriction evaluation."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(
        feature_name="staging_only_feat",
        enabled=True,
        allowed_environments=("staging",),
    )
    manager.register_feature(flag)

    assert manager.evaluate("staging_only_feat", active_env="development").enabled is False
    assert manager.evaluate("staging_only_feat", active_env="staging").enabled is True


def test_feature_flag_manager_evaluate_rollout_percentage():
    """Verify rollout percentage evaluation determinism."""
    manager = FeatureFlagManager()
    flag_0 = FeatureFlag(feature_name="rollout_0", enabled=True, rollout_percentage=0.0)
    flag_100 = FeatureFlag(feature_name="rollout_100", enabled=True, rollout_percentage=100.0)

    manager.register_feature(flag_0)
    manager.register_feature(flag_100)

    assert manager.evaluate("rollout_0", instance_id="user_123").enabled is False
    assert manager.evaluate("rollout_100", instance_id="user_123").enabled is True


def test_feature_flag_manager_evaluation_caching():
    """Verify caching of evaluation results and cache hits counter."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="cached_feat", enabled=True)
    manager.register_feature(flag)

    manager.evaluate("cached_feat")
    manager.evaluate("cached_feat")  # Hit cache

    assert manager.statistics().cache_hits == 1


def test_feature_flag_manager_health_and_statistics():
    """Verify FeatureFlagManager health and statistics."""
    manager = FeatureFlagManager()
    assert manager.health().is_healthy is True
    assert isinstance(manager.statistics(), FeatureStatistics)


# ============================================================================
# 4. Source Manager & Provider Profile/Feature Integration Tests (Phase 14.3.4)
# ============================================================================


def test_configuration_source_manager_profile_overrides_priority():
    """Verify profile overrides integrated into ConfigurationSourceManager."""
    manager = ConfigurationSourceManager()

    # Active profile "development" has override debug = True
    assert manager.get("debug") is True

    # Switch profile to "production" (has debug = False)
    manager.activate_profile("production")
    assert manager.get("debug") is False


def test_configuration_provider_profile_and_feature_delegation():
    """Verify ConfigurationProvider delegates profile switching and feature evaluation."""
    provider = ConfigurationProvider()
    flag = FeatureFlag(feature_name="prov_feat", enabled=True)
    provider.register_feature(flag)

    assert provider.is_feature_enabled("prov_feat") is True
    assert provider.activate_profile("production") is True
    assert provider.get_active_profile().profile_name == "production"


# ============================================================================
# 5. Schema & Resolver Foundation Tests
# ============================================================================


def test_configuration_schema_manager_register_and_get_schema():
    """Verify ConfigurationSchemaManager register_schema and get_schema methods."""
    manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="app.name", expected_type=str, default_value="Auralis")
    schema = ConfigurationSchema(schema_name="app_schema", definitions=(defn,))

    assert manager.register_schema(schema) is True
    assert manager.contains("app_schema") is True
    assert manager.get_definition("app.name") == defn


def test_configuration_resolver_convert_value_primitives():
    """Verify ConfigurationResolver type conversions for primitive types."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("123", int) == 123
    assert resolver.convert_value("3.14", float) == 3.14
    assert resolver.convert_value("hello", str) == "hello"
    assert resolver.convert_value("/tmp/config", Path) == Path("/tmp/config")


def test_configuration_validator_validate_required_keys():
    """Verify missing required key generates ConfigurationError."""
    schema_manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="secret_key", expected_type=str, required=True)
    schema_manager.register_schema(ConfigurationSchema(schema_name="auth", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    result = validator.validate({})

    assert result.is_valid is False
    assert len(result.errors) == 1


# ============================================================================
# 6. Concurrent Multithreaded Tests
# ============================================================================


def test_profile_manager_resolve_profile_missing_profile_raises():
    """Verify resolve_profile raises ConfigurationProfileError for missing profile."""
    manager = ProfileManager()
    with pytest.raises(ConfigurationProfileError):
        manager.resolve_profile("non_existent")


def test_profile_manager_list_profiles_returns_all():
    """Verify list_profiles returns all registered profiles."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    assert len(profiles) >= 3


def test_profile_manager_active_profile_init_default():
    """Verify ProfileManager initializes default active profile as development."""
    manager = ProfileManager()
    assert manager.get_active_profile().profile_name == "development"


def test_feature_flag_manager_toggle_missing_feature():
    """Verify toggle returns False for missing feature."""
    manager = FeatureFlagManager()
    assert manager.toggle("missing") is False


def test_feature_flag_manager_enable_missing_feature():
    """Verify enable returns False for missing feature."""
    manager = FeatureFlagManager()
    assert manager.enable("missing") is False


def test_feature_flag_manager_disable_missing_feature():
    """Verify disable returns False for missing feature."""
    manager = FeatureFlagManager()
    assert manager.disable("missing") is False


def test_feature_flag_manager_list_features_empty():
    """Verify list_features when no features registered."""
    manager = FeatureFlagManager()
    assert len(manager.list_features()) == 0


def test_configuration_source_manager_get_entry_from_profile_overrides():
    """Verify get_entry resolves key from active profile overrides."""
    manager = ConfigurationSourceManager()
    entry = manager.get_entry("debug")
    assert entry is not None
    assert entry.value is True
    assert "profile:" in entry.source_name


def test_configuration_source_manager_has_key_in_profile_overrides():
    """Verify has returns True for key present in active profile overrides."""
    manager = ConfigurationSourceManager()
    assert manager.has("debug") is True


def test_configuration_source_manager_get_all_includes_profile_overrides():
    """Verify get_all merges active profile overrides."""
    manager = ConfigurationSourceManager()
    all_vals = manager.get_all()
    assert "debug" in all_vals
    assert all_vals["debug"] is True


def test_configuration_source_manager_register_profile():
    """Verify ConfigurationSourceManager register_profile delegation."""
    manager = ConfigurationSourceManager()
    p = ConfigurationProfileDefinition(profile_name="staging", overrides={"env": "staging"})
    assert manager.register_profile(p) is True
    assert manager.activate_profile("staging") is True


def test_configuration_source_manager_register_feature():
    """Verify ConfigurationSourceManager register_feature delegation."""
    manager = ConfigurationSourceManager()
    f = FeatureFlag(feature_name="src_feat", enabled=True)
    assert manager.register_feature(f) is True
    assert manager.is_feature_enabled("src_feat") is True


def test_configuration_source_manager_profile_and_feature_properties():
    """Verify ConfigurationSourceManager profile_manager and feature_manager properties."""
    manager = ConfigurationSourceManager()
    assert isinstance(manager.profile_manager, ProfileManager)
    assert isinstance(manager.feature_manager, FeatureFlagManager)


def test_configuration_provider_activate_profile():
    """Verify ConfigurationProvider activate_profile delegation."""
    provider = ConfigurationProvider()
    assert provider.activate_profile("production") is True
    assert provider.get_active_profile().profile_name == "production"


def test_configuration_provider_register_profile():
    """Verify ConfigurationProvider register_profile delegation."""
    provider = ConfigurationProvider()
    p = ConfigurationProfileDefinition(profile_name="test_p", overrides={"a": 1})
    assert provider.register_profile(p) is True


def test_configuration_provider_register_feature():
    """Verify ConfigurationProvider register_feature delegation."""
    provider = ConfigurationProvider()
    f = FeatureFlag(feature_name="prov_f", enabled=True)
    assert provider.register_feature(f) is True
    assert provider.is_feature_enabled("prov_f") is True


def test_configuration_provider_diagnostics_includes_profile_and_feature_stats():
    """Verify ConfigurationProvider diagnostics includes profile and feature statistics."""
    provider = ConfigurationProvider()
    diag = provider.diagnostics()
    assert diag.profile_statistics is not None
    assert diag.feature_statistics is not None


def test_profile_definition_default_fields():
    """Verify ConfigurationProfileDefinition default fields."""
    p = ConfigurationProfileDefinition(profile_name="dev")
    assert p.profile_name == "dev"
    assert p.active is True


def test_profile_snapshot_creation_timestamp():
    """Verify ConfigurationProfileSnapshot timestamp generation."""
    snap = ConfigurationProfileSnapshot(active_profile_name="dev")
    assert snap.created_at is not None


def test_feature_flag_default_fields():
    """Verify FeatureFlag default fields."""
    f = FeatureFlag(feature_name="feat_x")
    assert f.enabled is True
    assert f.rollout_percentage == 100.0


def test_feature_evaluation_default_timestamp():
    """Verify FeatureEvaluation default timestamp."""
    ev = FeatureEvaluation(feature_name="x", enabled=True, reason="ok")
    assert ev.evaluated_at is not None


def test_profile_statistics_metrics_fields():
    """Verify ProfileStatistics default metric values."""
    stats = ProfileStatistics(registered_profiles_count=5)
    assert stats.registered_profiles_count == 5


def test_profile_health_checked_at():
    """Verify ProfileHealth checked_at generation."""
    h = ProfileHealth()
    assert h.checked_at is not None


def test_feature_statistics_metrics_fields():
    """Verify FeatureStatistics default metric values."""
    stats = FeatureStatistics(total_features=10, enabled_features=8)
    assert stats.total_features == 10
    assert stats.enabled_features == 8


def test_feature_health_checked_at():
    """Verify FeatureHealth checked_at generation."""
    h = FeatureHealth()
    assert h.checked_at is not None


def test_configuration_diagnostics_profile_and_feature_stats_integration():
    """Verify ConfigurationDiagnostics model holds profile and feature statistics."""
    diag = ConfigurationDiagnostics(
        profile_statistics=ProfileStatistics(registered_profiles_count=3),
        feature_statistics=FeatureStatistics(total_features=2),
    )
    assert diag.profile_statistics.registered_profiles_count == 3
    assert diag.feature_statistics.total_features == 2


def test_profile_manager_unregister_missing_profile_returns_false():
    """Verify unregister_profile returns False for missing profile."""
    manager = ProfileManager()
    assert manager.unregister_profile("non_existent_profile_123") is False


def test_profile_manager_activate_same_profile_noop():
    """Verify activating already active profile returns True."""
    manager = ProfileManager()
    assert manager.activate_profile("development") is True


def test_feature_flag_manager_enable_already_enabled_noop():
    """Verify enabling an already enabled feature flag returns True."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="enabled_f", enabled=True)
    manager.register_feature(flag)

    assert manager.enable("enabled_f") is True
    assert manager.is_enabled("enabled_f") is True


def test_feature_flag_manager_disable_already_disabled_noop():
    """Verify disabling an already disabled feature flag returns True."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="disabled_f", enabled=False)
    manager.register_feature(flag)

    assert manager.disable("disabled_f") is True
    assert manager.is_enabled("disabled_f") is False


def test_feature_flag_manager_toggle_disabled_to_enabled():
    """Verify toggle switches disabled feature flag to enabled."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="toggle_test_f", enabled=False)
    manager.register_feature(flag)

    assert manager.toggle("toggle_test_f") is True
    assert manager.is_enabled("toggle_test_f") is True


def test_feature_flag_manager_evaluate_profile_restriction_pass():
    """Verify profile restriction evaluation when matching active profile."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(
        feature_name="dev_feat",
        enabled=True,
        allowed_profiles=(ConfigurationProfileType.DEVELOPMENT,),
    )
    manager.register_feature(flag)

    eval_res = manager.evaluate("dev_feat", active_profile_name="development")
    assert eval_res.enabled is True


def test_feature_flag_manager_evaluate_environment_restriction_pass():
    """Verify environment restriction evaluation when matching active environment."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(
        feature_name="staging_feat",
        enabled=True,
        allowed_environments=("staging",),
    )
    manager.register_feature(flag)

    eval_res = manager.evaluate("staging_feat", active_env="staging")
    assert eval_res.enabled is True


def test_feature_flag_manager_evaluate_rollout_50_percent():
    """Verify rollout percentage deterministic score evaluation."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="rollout_50", enabled=True, rollout_percentage=50.0)
    manager.register_feature(flag)

    eval_res = manager.evaluate("rollout_50", instance_id="user_test_id")
    assert isinstance(eval_res.enabled, bool)


def test_feature_flag_manager_evaluate_disabled_flag_reason():
    """Verify reason text for explicitly disabled flag."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="dis_feat", enabled=False)
    manager.register_feature(flag)

    eval_res = manager.evaluate("dis_feat")
    assert eval_res.enabled is False
    assert "explicitly disabled" in eval_res.reason


def test_feature_flag_manager_evaluate_missing_flag_reason():
    """Verify reason text for missing flag."""
    manager = FeatureFlagManager()
    eval_res = manager.evaluate("missing_feat_xyz")
    assert eval_res.enabled is False
    assert "not registered" in eval_res.reason


def test_feature_flag_manager_evaluate_dependency_missing():
    """Verify dependency feature flag missing evaluates to disabled."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="child_feat_a", enabled=True, dependencies=("missing_parent_feat",))
    manager.register_feature(flag)

    eval_res = manager.evaluate("child_feat_a")
    assert eval_res.enabled is False
    assert "disabled" in eval_res.reason


def test_feature_flag_manager_evaluate_dependency_disabled():
    """Verify dependency feature flag disabled evaluates to disabled."""
    manager = FeatureFlagManager()
    parent = FeatureFlag(feature_name="parent_b", enabled=False)
    child = FeatureFlag(feature_name="child_b", enabled=True, dependencies=("parent_b",))
    manager.register_feature(parent)
    manager.register_feature(child)

    eval_res = manager.evaluate("child_b")
    assert eval_res.enabled is False


def test_feature_flag_manager_evaluate_dependency_enabled():
    """Verify dependency feature flag enabled evaluates to enabled."""
    manager = FeatureFlagManager()
    parent = FeatureFlag(feature_name="parent_c", enabled=True)
    child = FeatureFlag(feature_name="child_c", enabled=True, dependencies=("parent_c",))
    manager.register_feature(parent)
    manager.register_feature(child)

    eval_res = manager.evaluate("child_c")
    assert eval_res.enabled is True


def test_feature_flag_manager_cache_invalidation_on_enable():
    """Verify cache invalidation on feature flag enable."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="cache_feat", enabled=False)
    manager.register_feature(flag)

    assert manager.is_enabled("cache_feat") is False
    manager.enable("cache_feat")
    assert manager.is_enabled("cache_feat") is True


def test_feature_flag_manager_cache_invalidation_on_disable():
    """Verify cache invalidation on feature flag disable."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="cache_feat_2", enabled=True)
    manager.register_feature(flag)

    assert manager.is_enabled("cache_feat_2") is True
    manager.disable("cache_feat_2")
    assert manager.is_enabled("cache_feat_2") is False


def test_feature_flag_manager_cache_invalidation_on_register():
    """Verify cache invalidation on feature flag register."""
    manager = FeatureFlagManager()
    flag1 = FeatureFlag(feature_name="cache_feat_3", enabled=False)
    manager.register_feature(flag1)

    assert manager.is_enabled("cache_feat_3") is False
    flag2 = FeatureFlag(feature_name="cache_feat_3", enabled=True)
    manager.register_feature(flag2)
    assert manager.is_enabled("cache_feat_3") is True


def test_feature_flag_manager_cache_invalidation_on_remove():
    """Verify cache invalidation on feature flag remove."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="cache_feat_4", enabled=True)
    manager.register_feature(flag)

    assert manager.is_enabled("cache_feat_4") is True
    manager.remove_feature("cache_feat_4")
    assert manager.is_enabled("cache_feat_4") is False


def test_configuration_source_manager_get_entry_miss_returns_none():
    """Verify get_entry returns None for completely absent key."""
    manager = ConfigurationSourceManager()
    assert manager.get_entry("absent_key_12345") is None


def test_configuration_source_manager_get_all_merges_in_priority_order():
    """Verify get_all merges profile overrides and sources in priority order."""
    manager = ConfigurationSourceManager()
    mem_src = manager.registry.get_source("memory_source")
    assert isinstance(mem_src, MemoryConfigurationSource)
    mem_src.set("custom_port", 9000)

    all_vals = manager.get_all()
    assert all_vals["custom_port"] == 9000


def test_configuration_source_manager_health_reporting_with_profiles_and_features():
    """Verify ConfigurationSourceManager health assessment incorporating sources, profiles, and features."""
    manager = ConfigurationSourceManager()
    health = manager.health()
    assert health.is_healthy is True


def test_configuration_source_manager_statistics_includes_profile_and_feature_counts():
    """Verify ConfigurationSourceManager statistics incorporating profiles and features metrics."""
    manager = ConfigurationSourceManager()
    stats = manager.statistics()
    assert "profiles_count" in stats.metrics
    assert "features_count" in stats.metrics


def test_configuration_provider_shutdown_and_restart():
    """Verify ConfigurationProvider shutdown and restart state transitions."""
    provider = ConfigurationProvider()
    provider.initialize()
    assert provider.health().state == ConfigurationRuntimeState.READY

    provider.shutdown()
    assert provider.health().state == ConfigurationRuntimeState.STOPPED

    provider.restart()
    assert provider.health().state == ConfigurationRuntimeState.READY


def test_configuration_provider_capabilities_flags():
    """Verify ConfigurationProvider capabilities declaration flags."""
    provider = ConfigurationProvider()
    caps = provider.capabilities()
    assert caps.supports_dotenv is True
    assert caps.supports_json is True
    assert caps.supports_yaml is True


def test_configuration_provider_get_context_environment():
    """Verify ConfigurationProvider get_context environment snapshot."""
    provider = ConfigurationProvider()
    ctx = provider.get_context()
    assert ctx.environment == ConfigurationProfileType.DEVELOPMENT


def test_configuration_runtime_provider_property():
    """Verify ConfigurationRuntime provider property."""
    runtime = ConfigurationRuntime()
    assert isinstance(runtime.provider, IConfigurationProvider)


def test_configuration_runtime_restart_lifecycle():
    """Verify ConfigurationRuntime restart lifecycle transition."""
    runtime = ConfigurationRuntime()
    runtime.initialize()
    state = runtime.restart()
    assert state == ConfigurationRuntimeState.READY


def test_configuration_runtime_health_assessment():
    """Verify ConfigurationRuntime health assessment report."""
    runtime = ConfigurationRuntime()
    runtime.initialize()
    health = runtime.health()
    assert health.is_healthy is True
    assert health.state == ConfigurationRuntimeState.READY


def test_configuration_runtime_statistics_delegation():
    """Verify ConfigurationRuntime statistics delegation."""
    runtime = ConfigurationRuntime()
    stats = runtime.statistics()
    assert isinstance(stats, ConfigurationStatistics)


def test_configuration_runtime_diagnostics_delegation():
    """Verify ConfigurationRuntime diagnostics delegation."""
    runtime = ConfigurationRuntime()
    diag = runtime.diagnostics()
    assert isinstance(diag, ConfigurationDiagnostics)


def test_configuration_runtime_context_snapshot():
    """Verify ConfigurationRuntime context snapshot."""
    runtime = ConfigurationRuntime()
    ctx = runtime.context()
    assert isinstance(ctx, ConfigurationContext)


def test_lazy_singletons_set_and_reset_runtime():
    """Verify set_configuration_runtime and reset_configuration_runtime."""
    reset_configuration_runtime()
    reset_configuration_provider()

    custom_runtime = ConfigurationRuntime()
    set_configuration_runtime(custom_runtime)
    assert get_configuration_runtime() is custom_runtime

    reset_configuration_runtime()
    reset_configuration_provider()


def test_lazy_singletons_set_and_reset_provider():
    """Verify set_configuration_provider and reset_configuration_provider."""
    reset_configuration_runtime()
    reset_configuration_provider()

    custom_provider = ConfigurationProvider()
    set_configuration_provider(custom_provider)
    assert get_configuration_provider() is custom_provider

    reset_configuration_runtime()
    reset_configuration_provider()


def test_memory_source_statistics_counters():
    """Verify MemoryConfigurationSource statistics lookup counters."""
    source = MemoryConfigurationSource()
    source.set("key_a", "val_a")

    source.get("key_a")
    source.get("key_missing")

    stats = source.statistics()
    assert stats.lookups_count == 2
    assert stats.hits_count == 1
    assert stats.misses_count == 1


def test_environment_source_contains_key():
    """Verify EnvironmentConfigurationSource contains key check."""
    os.environ["ENV_CONTAINS_TEST"] = "1"
    try:
        source = EnvironmentConfigurationSource()
        assert source.contains("ENV_CONTAINS_TEST") is True
        assert source.contains("ENV_ABSENT_TEST_KEY_XYZ") is False
    finally:
        del os.environ["ENV_CONTAINS_TEST"]


def test_environment_source_values():
    """Verify EnvironmentConfigurationSource values method."""
    source = EnvironmentConfigurationSource()
    vals = source.values()
    assert isinstance(vals, tuple)


def test_environment_source_items():
    """Verify EnvironmentConfigurationSource items method."""
    source = EnvironmentConfigurationSource()
    items = source.items()
    assert isinstance(items, tuple)


def test_dotenv_source_keys_values_items():
    """Verify DotEnvConfigurationSource keys, values, and items methods."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env") as tmp:
        tmp.write("FOO=BAR\nBAZ=QUX\n")
        tmp_path = tmp.name

    try:
        source = DotEnvConfigurationSource(filepath=tmp_path)
        assert len(source.keys()) == 2
        assert len(source.values()) == 2
        assert len(source.items()) == 2
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_source_registry_get_source():
    """Verify SourceRegistry get_source method."""
    registry = SourceRegistry()
    src = MemoryConfigurationSource(source_name="target_src")
    registry.register_source(src)

    assert registry.get_source("target_src") is src
    assert registry.get_source("missing_src") is None


def test_source_registry_unregister_source():
    """Verify SourceRegistry unregister_source method."""
    registry = SourceRegistry()
    src = MemoryConfigurationSource(source_name="target_unreg")
    registry.register_source(src)

    assert registry.unregister_source("target_unreg") is True
    assert registry.contains("target_unreg") is False


def test_configuration_schema_manager_list_schemas():
    """Verify ConfigurationSchemaManager list_schemas method."""
    manager = ConfigurationSchemaManager()
    schema = ConfigurationSchema(schema_name="listed_schema")
    manager.register_schema(schema)

    schemas = manager.list_schemas()
    assert len(schemas) == 1
    assert schemas[0].schema_name == "listed_schema"


def test_configuration_resolver_convert_value_enum_by_value():
    """Verify Enum conversion by enum string value."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("local", SampleEnvEnum) == SampleEnvEnum.LOCAL


def test_configuration_resolver_resolve_all_missing_required_key():
    """Verify resolve_all tracks missing required keys."""
    schema_manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="req_key", expected_type=str, required=True)
    schema_manager.register_schema(ConfigurationSchema(schema_name="req_schema", definitions=(defn,)))

    resolver = ConfigurationResolver(schema_manager=schema_manager)
    result = resolver.resolve_all({})

    assert len(result.missing_required_keys) == 1
    assert result.missing_required_keys[0] == "req_key"


def test_configuration_validator_validate_property_min_length_violation():
    """Verify ConfigurationValidator min_length string constraint violation."""
    validator = ConfigurationValidator()
    defn = ConfigurationDefinition(key="s", expected_type=str, constraint=ConfigurationConstraint(min_length=5))
    errs, _ = validator.validate_property("s", "abc", defn)

    assert len(errs) == 1
    assert errs[0].error_type == "MIN_LENGTH_VIOLATION"


def test_configuration_validator_validate_property_max_length_violation():
    """Verify ConfigurationValidator max_length string constraint violation."""
    validator = ConfigurationValidator()
    defn = ConfigurationDefinition(key="s", expected_type=str, constraint=ConfigurationConstraint(max_length=3))
    errs, _ = validator.validate_property("s", "abcdef", defn)

    assert len(errs) == 1
    assert errs[0].error_type == "MAX_LENGTH_VIOLATION"


def test_configuration_validator_validate_property_regex_mismatch():
    """Verify ConfigurationValidator regex mismatch error."""
    validator = ConfigurationValidator()
    defn = ConfigurationDefinition(key="digits", expected_type=str, constraint=ConfigurationConstraint(regex_pattern=r"^\d+$"))
    errs, _ = validator.validate_property("digits", "abc", defn)

    assert len(errs) == 1
    assert errs[0].error_type == "REGEX_MISMATCH"


def test_concurrent_profile_activation():
    """Verify thread-safe concurrent profile activations."""
    manager = ProfileManager()

    def do_switch(name: str):
        return manager.activate_profile(name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_switch, "production" if i % 2 == 0 else "development") for i in range(20)]
        results = [f.result() for f in futures]

    assert all(r is True for r in results)


def test_concurrent_feature_evaluations():
    """Verify thread-safe concurrent feature flag evaluations."""
    manager = FeatureFlagManager()
    flag = FeatureFlag(feature_name="concurrent_feat", enabled=True)
    manager.register_feature(flag)

    def do_eval(i: int):
        return manager.evaluate("concurrent_feat", instance_id=f"user_{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_eval, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.enabled is True for r in results)


def test_concurrent_configuration_runtime_init_shutdown():
    """Verify thread-safe concurrent initialize and shutdown on ConfigurationRuntime."""
    runtime = ConfigurationRuntime()

    def do_init_shutdown():
        runtime.initialize()
        return runtime.shutdown()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_init_shutdown) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r == ConfigurationRuntimeState.STOPPED for r in results)
