"""Comprehensive unit tests for Phase 14.3.3 Configuration Resolution & Validation Engine."""

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
    ResolutionStatistics,
    SourceHealth,
    SourcePriority,
    SourceRegistration,
    SourceStatistics,
    ValidationStatistics,
)
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


def test_configuration_models_immutability():
    """Verify Pydantic v2 model immutability with ConfigDict(frozen=True)."""
    state = ConfigurationState(state=ConfigurationRuntimeState.READY)
    assert state.state == ConfigurationRuntimeState.READY

    with pytest.raises(ValidationError):
        state.state = ConfigurationRuntimeState.STOPPED  # type: ignore[misc]


def test_configuration_entry_model_immutability():
    """Verify ConfigurationEntry model attributes and immutability."""
    entry = ConfigurationEntry(
        key="app.name",
        value="Auralis",
        source_name="memory",
        source_type=ConfigurationSourceType.MEMORY,
        priority=500,
    )
    assert entry.key == "app.name"
    assert entry.value == "Auralis"
    assert entry.priority == 500

    with pytest.raises(ValidationError):
        entry.key = "modified"  # type: ignore[misc]


def test_configuration_snapshot_model_immutability():
    """Verify ConfigurationSnapshot model attributes and immutability."""
    snapshot = ConfigurationSnapshot(values={"key": "val"})
    assert snapshot.values["key"] == "val"
    assert snapshot.created_at is not None


def test_configuration_error_and_warning_models():
    """Verify ConfigurationError and ConfigurationWarning models."""
    err = ConfigurationError(key="db.port", message="Invalid port", error_type="TYPE_ERROR")
    warn = ConfigurationWarning(key="db.host", message="Using default localhost")

    assert err.key == "db.port"
    assert warn.warning_type == "DEFAULT_APPLIED"


def test_configuration_constraint_and_definition_defaults():
    """Verify ConfigurationConstraint and ConfigurationDefinition default values."""
    constraint = ConfigurationConstraint(min_value=1, max_value=100)
    defn = ConfigurationDefinition(key="server.port", expected_type=int, default_value=8080, constraint=constraint)

    assert defn.key == "server.port"
    assert defn.default_value == 8080
    assert defn.constraint.min_value == 1


def test_resolution_and_validation_statistics_models():
    """Verify ResolutionStatistics and ValidationStatistics models."""
    res_stats = ResolutionStatistics(resolution_count=5, conversion_count=2)
    val_stats = ValidationStatistics(validation_count=3, successful_validations=3)

    assert res_stats.resolution_count == 5
    assert val_stats.successful_validations == 3


def test_configuration_resolution_result_model_immutability():
    """Verify ConfigurationResolutionResult model fields."""
    res = ConfigurationResolutionResult(resolved_values={"a": 1}, converted_keys=("a",))
    assert res.resolved_values["a"] == 1
    assert res.converted_keys == ("a",)


def test_configuration_validation_result_model_immutability():
    """Verify ConfigurationValidationResult model fields."""
    val = ConfigurationValidationResult(is_valid=True)
    assert val.is_valid is True
    assert val.errors == ()


def test_configuration_capabilities_defaults():
    """Verify ConfigurationCapabilities default flags."""
    caps = ConfigurationCapabilities()
    assert caps.supports_dotenv is True
    assert caps.supports_json is True
    assert caps.supports_yaml is True
    assert caps.supports_environment_override is True
    assert caps.supports_hot_reload is True
    assert caps.supports_secret_masking is True


def test_configuration_health_and_statistics_models():
    """Verify ConfigurationHealth and ConfigurationStatistics model attributes."""
    health = ConfigurationHealth(is_healthy=True, state=ConfigurationRuntimeState.READY)
    assert health.is_healthy is True
    assert health.state == ConfigurationRuntimeState.READY

    stats = ConfigurationStatistics(total_properties_loaded=10, reload_count=2)
    assert stats.total_properties_loaded == 10
    assert stats.reload_count == 2


def test_configuration_context_and_profile_models():
    """Verify ConfigurationContext and ConfigurationProfile models."""
    context = ConfigurationContext(app_name="AuralisTest", environment=ConfigurationProfileType.TESTING)
    assert context.app_name == "AuralisTest"
    assert context.environment == ConfigurationProfileType.TESTING

    profile = ConfigurationProfile(profile_type=ConfigurationProfileType.PRODUCTION, profile_name="prod")
    assert profile.profile_type == ConfigurationProfileType.PRODUCTION
    assert profile.profile_name == "prod"


def test_configuration_diagnostics_model():
    """Verify ConfigurationDiagnostics model initialization."""
    diag = ConfigurationDiagnostics(
        state=ConfigurationRuntimeState.READY,
        active_profile_name="development",
        active_sources_count=2,
    )
    assert diag.state == ConfigurationRuntimeState.READY
    assert diag.active_profile_name == "development"
    assert diag.active_sources_count == 2


# ============================================================================
# 2. Exception Hierarchy Tests
# ============================================================================


def test_configuration_exception_hierarchy():
    """Verify ConfigurationException subclass hierarchy."""
    assert issubclass(ConfigurationInitializationError, ConfigurationException)
    assert issubclass(ConfigurationValidationError, ConfigurationException)
    assert issubclass(ConfigurationProviderError, ConfigurationException)
    assert issubclass(ConfigurationProfileError, ConfigurationException)
    assert issubclass(ConfigurationSourceError, ConfigurationException)


# ============================================================================
# 3. ABC Interfaces Tests
# ============================================================================


def test_configuration_interfaces_instantiation_raises():
    """Verify direct instantiation of ABC interfaces raises TypeError."""
    with pytest.raises(TypeError):
        IConfigurationSource()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationDiagnostics()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationValidator()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationManager()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IConfigurationRuntime()  # type: ignore[abstract]


# ============================================================================
# 4. Configuration Schema Manager Tests (Phase 14.3.3)
# ============================================================================


def test_configuration_schema_manager_register_and_get_schema():
    """Verify ConfigurationSchemaManager register_schema and get_schema methods."""
    manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="app.name", expected_type=str, default_value="Auralis")
    schema = ConfigurationSchema(schema_name="app_schema", definitions=(defn,))

    assert manager.register_schema(schema) is True
    assert manager.contains("app_schema") is True
    assert manager.get_definition("app.name") == defn


def test_configuration_schema_manager_duplicate_schema_raises():
    """Verify registering duplicate schema_name raises ConfigurationValidationError."""
    manager = ConfigurationSchemaManager()
    schema1 = ConfigurationSchema(schema_name="db_schema")
    schema2 = ConfigurationSchema(schema_name="db_schema")

    manager.register_schema(schema1)
    with pytest.raises(ConfigurationValidationError):
        manager.register_schema(schema2)


def test_configuration_schema_manager_invalid_schema_name_raises():
    """Verify registering schema with empty name raises ConfigurationValidationError."""
    manager = ConfigurationSchemaManager()
    schema = ConfigurationSchema(schema_name="")
    with pytest.raises(ConfigurationValidationError):
        manager.register_schema(schema)


def test_configuration_schema_manager_unregister_schema():
    """Verify unregistering schema updates cached definitions."""
    manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="k1", expected_type=int)
    schema = ConfigurationSchema(schema_name="s1", definitions=(defn,))

    manager.register_schema(schema)
    assert manager.get_definition("k1") is not None

    manager.unregister_schema("s1")
    assert manager.get_definition("k1") is None


def test_configuration_schema_manager_get_all_definitions():
    """Verify get_all_definitions returns all cached definitions."""
    manager = ConfigurationSchemaManager()
    defn1 = ConfigurationDefinition(key="k1", expected_type=int)
    defn2 = ConfigurationDefinition(key="k2", expected_type=str)
    manager.register_schema(ConfigurationSchema(schema_name="s1", definitions=(defn1, defn2)))

    defs = manager.get_all_definitions()
    assert len(defs) == 2


def test_configuration_schema_manager_clear():
    """Verify clear empties all schemas and cached definitions."""
    manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="k1", expected_type=int)
    schema = ConfigurationSchema(schema_name="s1", definitions=(defn,))
    manager.register_schema(schema)

    manager.clear()
    assert len(manager.list_schemas()) == 0
    assert manager.get_definition("k1") is None


# ============================================================================
# 5. Configuration Resolver Engine Tests (Phase 14.3.3)
# ============================================================================


def test_configuration_resolver_convert_value_primitives():
    """Verify ConfigurationResolver type conversions for primitive types."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("123", int) == 123
    assert resolver.convert_value("3.14", float) == 3.14
    assert resolver.convert_value("hello", str) == "hello"
    assert resolver.convert_value("/tmp/config", Path) == Path("/tmp/config")


def test_configuration_resolver_float_and_int_conversions():
    """Verify float from int and int from float conversion."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value(10, float) == 10.0
    assert resolver.convert_value(10.5, int) == 10


def test_configuration_resolver_boolean_conversion_variations():
    """Verify boolean conversion for case-insensitive variations."""
    resolver = ConfigurationResolver()
    for true_val in ("true", "TRUE", "True", "1", "yes", "YES", "on", "ON"):
        assert resolver.convert_value(true_val, bool) is True

    for false_val in ("false", "FALSE", "False", "0", "no", "NO", "off", "OFF"):
        assert resolver.convert_value(false_val, bool) is False

    with pytest.raises(ValueError):
        resolver.convert_value("invalid_bool", bool)


def test_configuration_resolver_convert_value_containers():
    """Verify container type conversions (list, tuple, set)."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("a,b,c", list) == ["a", "b", "c"]
    assert resolver.convert_value("x,y", tuple) == ("x", "y")
    assert resolver.convert_value("1,2,2", set) == {"1", "2"}

    assert resolver.convert_value(["a", "b"], list) == ["a", "b"]
    assert resolver.convert_value(("x", "y"), tuple) == ("x", "y")
    assert resolver.convert_value({"1", "2"}, set) == {"1", "2"}


def test_configuration_resolver_enum_and_timedelta_conversion():
    """Verify Enum and timedelta conversions."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("local", SampleEnvEnum) == SampleEnvEnum.LOCAL
    assert resolver.convert_value(SampleEnvEnum.PROD, SampleEnvEnum) == SampleEnvEnum.PROD
    assert resolver.convert_value(60, timedelta) == timedelta(seconds=60)
    assert resolver.convert_value("120", timedelta) == timedelta(seconds=120)


def test_configuration_resolver_resolve_key_default_fallback():
    """Verify resolve_key applies default fallback when raw value is None."""
    resolver = ConfigurationResolver()
    val = resolver.resolve_key("missing.port", None, expected_type=int, default=8080)
    assert val == 8080


def test_configuration_resolver_resolve_key_missing_no_default():
    """Verify resolve_key returns None when missing and no default."""
    resolver = ConfigurationResolver()
    val = resolver.resolve_key("missing.key", None, expected_type=str)
    assert val is None


def test_configuration_resolver_type_mismatch_fallback():
    """Verify type mismatch falls back to default if provided."""
    resolver = ConfigurationResolver()
    val = resolver.resolve_key("invalid.int", "not_an_int", expected_type=int, default=10)
    assert val == 10


def test_configuration_resolver_resolve_all_against_schema():
    """Verify resolve_all converts properties and applies schema defaults."""
    schema_manager = ConfigurationSchemaManager()
    defn1 = ConfigurationDefinition(key="port", expected_type=int, default_value=5000)
    defn2 = ConfigurationDefinition(key="debug", expected_type=bool, default_value=False)
    schema_manager.register_schema(ConfigurationSchema(schema_name="server", definitions=(defn1, defn2)))

    resolver = ConfigurationResolver(schema_manager=schema_manager)
    result = resolver.resolve_all({"port": "9000"})

    assert result.resolved_values["port"] == 9000
    assert result.resolved_values["debug"] is False
    assert "port" in result.converted_keys
    assert "debug" in result.defaulted_keys


def test_configuration_resolver_statistics():
    """Verify resolver statistics metrics tracking."""
    resolver = ConfigurationResolver()
    resolver.resolve_key("key1", "100", expected_type=int)
    resolver.resolve_key("key2", None, expected_type=str, default="fallback")

    stats = resolver.statistics()
    assert stats.resolution_count == 2
    assert stats.conversion_count == 1
    assert stats.default_applications == 1


# ============================================================================
# 6. Configuration Validator Engine Tests (Phase 14.3.3)
# ============================================================================


def test_configuration_validator_validate_required_keys():
    """Verify missing required key generates ConfigurationError."""
    schema_manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="secret_key", expected_type=str, required=True)
    schema_manager.register_schema(ConfigurationSchema(schema_name="auth", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    result = validator.validate({})

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].error_type == "MISSING_REQUIRED_KEY"


def test_configuration_validator_missing_key_warning():
    """Verify missing optional key with default generates warning."""
    schema_manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="host", expected_type=str, required=False, default_value="localhost")
    schema_manager.register_schema(ConfigurationSchema(schema_name="net", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    result = validator.validate({})

    assert result.is_valid is True
    assert len(result.warnings) == 1
    assert result.warnings[0].warning_type == "DEFAULT_APPLIED"


def test_configuration_validator_allowed_values_constraint():
    """Verify allowed_values constraint violation."""
    schema_manager = ConfigurationSchemaManager()
    constraint = ConfigurationConstraint(allowed_values=("dev", "prod"))
    defn = ConfigurationDefinition(key="env", expected_type=str, constraint=constraint)
    schema_manager.register_schema(ConfigurationSchema(schema_name="env_schema", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    res_valid = validator.validate({"env": "dev"})
    assert res_valid.is_valid is True

    res_invalid = validator.validate({"env": "invalid_env"})
    assert res_invalid.is_valid is False
    assert res_invalid.errors[0].error_type == "ALLOWED_VALUES_VIOLATION"


def test_configuration_validator_min_max_value_constraints():
    """Verify min_value and max_value constraints."""
    schema_manager = ConfigurationSchemaManager()
    constraint = ConfigurationConstraint(min_value=10, max_value=100)
    defn = ConfigurationDefinition(key="count", expected_type=int, constraint=constraint)
    schema_manager.register_schema(ConfigurationSchema(schema_name="count_schema", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    assert validator.validate({"count": 50}).is_valid is True
    assert validator.validate({"count": 5}).is_valid is False
    assert validator.validate({"count": 200}).is_valid is False


def test_configuration_validator_string_length_constraints():
    """Verify min_length and max_length string constraints."""
    schema_manager = ConfigurationSchemaManager()
    constraint = ConfigurationConstraint(min_length=3, max_length=10)
    defn = ConfigurationDefinition(key="username", expected_type=str, constraint=constraint)
    schema_manager.register_schema(ConfigurationSchema(schema_name="user_schema", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    assert validator.validate({"username": "auralis"}).is_valid is True
    assert validator.validate({"username": "ab"}).is_valid is False
    assert validator.validate({"username": "very_long_username_here"}).is_valid is False


def test_configuration_validator_regex_pattern_constraint():
    """Verify regex_pattern constraint matching."""
    schema_manager = ConfigurationSchemaManager()
    constraint = ConfigurationConstraint(regex_pattern=r"^v\d+\.\d+$")
    defn = ConfigurationDefinition(key="version", expected_type=str, constraint=constraint)
    schema_manager.register_schema(ConfigurationSchema(schema_name="ver_schema", definitions=(defn,)))

    validator = ConfigurationValidator(schema_manager=schema_manager)
    assert validator.validate({"version": "v1.0"}).is_valid is True
    assert validator.validate({"version": "1.0"}).is_valid is False


def test_configuration_validator_statistics():
    """Verify validator statistics metrics tracking."""
    validator = ConfigurationValidator()
    validator.validate({})
    stats = validator.statistics()

    assert stats.validation_count == 1
    assert stats.successful_validations == 1


# ============================================================================
# 7. Source Manager & Provider Integration Tests (Phase 14.3.3)
# ============================================================================


def test_configuration_source_manager_resolve_and_validate():
    """Verify ConfigurationSourceManager resolve, resolve_all, and validate."""
    manager = ConfigurationSourceManager()
    defn = ConfigurationDefinition(key="server.port", expected_type=int, default_value=8000)
    manager.register_schema(ConfigurationSchema(schema_name="server", definitions=(defn,)))

    assert manager.resolve("server.port") == 8000
    res_all = manager.resolve_all()
    assert res_all.resolved_values["server.port"] == 8000

    val_res = manager.validate()
    assert val_res.is_valid is True


def test_configuration_source_manager_properties():
    """Verify ConfigurationSourceManager schema_manager, resolver, and validator properties."""
    manager = ConfigurationSourceManager()
    assert isinstance(manager.schema_manager, ConfigurationSchemaManager)
    assert isinstance(manager.resolver, ConfigurationResolver)
    assert isinstance(manager.validator, ConfigurationValidator)


def test_configuration_provider_schema_delegation():
    """Verify ConfigurationProvider delegates register_schema, resolve, and validate."""
    provider = ConfigurationProvider()
    defn = ConfigurationDefinition(key="max_connections", expected_type=int, default_value=20)
    provider.register_schema(ConfigurationSchema(schema_name="db", definitions=(defn,)))

    assert provider.resolve("max_connections") == 20
    assert provider.validate().is_valid is True


def test_configuration_provider_resolve_all():
    """Verify ConfigurationProvider resolve_all method."""
    provider = ConfigurationProvider()
    defn = ConfigurationDefinition(key="timeout", expected_type=int, default_value=30)
    provider.register_schema(ConfigurationSchema(schema_name="timeout_schema", definitions=(defn,)))

    res_all = provider.resolve_all()
    assert res_all.resolved_values["timeout"] == 30


# ============================================================================
# 8. Existing Sources & Registry Foundation Tests
# ============================================================================


def test_memory_configuration_source_set_get_remove_clear():
    """Verify MemoryConfigurationSource mutation and lookup methods."""
    source = MemoryConfigurationSource(initial_values={"key1": "val1"})
    assert source.contains("key1") is True
    assert source.get("key1") == "val1"

    source.set("key2", 42)
    assert source.get("key2") == 42
    assert len(source.keys()) == 2

    assert source.remove("key1") is True
    assert source.contains("key1") is False

    source.clear()
    assert len(source.keys()) == 0


def test_environment_configuration_source_reads():
    """Verify EnvironmentConfigurationSource reads from os.environ."""
    os.environ["AURALIS_TEST_ENV_KEY"] = "env_value_123"
    try:
        source = EnvironmentConfigurationSource()
        assert source.contains("AURALIS_TEST_ENV_KEY") is True
        assert source.get("AURALIS_TEST_ENV_KEY") == "env_value_123"
    finally:
        del os.environ["AURALIS_TEST_ENV_KEY"]


def test_dotenv_configuration_source_file_reading():
    """Verify DotEnvConfigurationSource reads from a temporary .env file."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env") as tmp:
        tmp.write("DB_HOST=localhost\nDB_PORT=5432\n# Comment line\n")
        tmp_path = tmp.name

    try:
        source = DotEnvConfigurationSource(filepath=tmp_path)
        assert source.contains("DB_HOST") is True
        assert source.get("DB_HOST") == "localhost"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_source_registry_registration_and_priority_sorting():
    """Verify SourceRegistry registering and sorting sources by priority descending."""
    registry = SourceRegistry()
    src_dotenv = DotEnvConfigurationSource(priority=300)
    src_memory = MemoryConfigurationSource(priority=500)
    src_env = EnvironmentConfigurationSource(priority=400)

    registry.register_source(src_dotenv)
    registry.register_source(src_memory)
    registry.register_source(src_env)

    sorted_sources = registry.sort_sources()
    assert sorted_sources[0].priority == 500
    assert sorted_sources[1].priority == 400
    assert sorted_sources[2].priority == 300


def test_configuration_runtime_lifecycle():
    """Verify ConfigurationRuntime lifecycle transitions."""
    runtime = ConfigurationRuntime()
    assert runtime.health().state == ConfigurationRuntimeState.UNINITIALIZED

    ready_state = runtime.initialize()
    assert ready_state == ConfigurationRuntimeState.READY
    assert runtime.health().is_healthy is True

    stopped_state = runtime.shutdown()
    assert stopped_state == ConfigurationRuntimeState.STOPPED


def test_configuration_runtime_lazy_singletons():
    """Verify get_configuration_runtime, set_configuration_runtime, reset_configuration_runtime."""
    reset_configuration_runtime()
    reset_configuration_provider()

    runtime = get_configuration_runtime()
    assert isinstance(runtime, IConfigurationRuntime)

    reset_configuration_runtime()
    reset_configuration_provider()


def test_configuration_resolver_passthrough_unknown_types():
    """Verify unknown target type passes through raw value."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value("raw", None) == "raw"


def test_configuration_resolver_none_input_value():
    """Verify None input value returns None."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value(None, int) is None


def test_configuration_resolver_dict_conversion():
    """Verify dict conversion."""
    resolver = ConfigurationResolver()
    assert resolver.convert_value({"a": 1}, dict) == {"a": 1}


def test_configuration_validator_regex_caching():
    """Verify regex pattern caching in ConfigurationValidator."""
    validator = ConfigurationValidator()
    pat1 = validator._get_regex(r"^\d+$")
    pat2 = validator._get_regex(r"^\d+$")
    assert pat1 is pat2


def test_configuration_validator_empty_values_dict():
    """Verify validating empty values dict against empty schema."""
    validator = ConfigurationValidator()
    res = validator.validate({})
    assert res.is_valid is True


def test_configuration_schema_manager_get_schema_missing():
    """Verify get_schema returns None for missing schema."""
    manager = ConfigurationSchemaManager()
    assert manager.get_schema("missing_schema") is None


def test_configuration_source_manager_validate_schema_override():
    """Verify validate with explicit schema parameter."""
    manager = ConfigurationSourceManager()
    defn = ConfigurationDefinition(key="override_key", expected_type=str, required=True)
    schema = ConfigurationSchema(schema_name="override_schema", definitions=(defn,))

    res_invalid = manager.validate(schema=schema)
    assert res_invalid.is_valid is False


def test_configuration_source_manager_create_snapshot_metadata():
    """Verify create_snapshot includes sources metadata."""
    manager = ConfigurationSourceManager()
    snap = manager.create_snapshot()
    assert len(snap.sources_metadata) == 3


def test_configuration_provider_diagnostics_timestamp():
    """Verify ConfigurationProvider diagnostics contains valid timestamp."""
    provider = ConfigurationProvider()
    diag = provider.diagnostics()
    assert diag.timestamp is not None


def test_configuration_provider_health_uninitialized():
    """Verify ConfigurationProvider health status when uninitialized."""
    provider = ConfigurationProvider()
    assert provider.health().is_healthy is True


def test_configuration_provider_statistics_reload_count():
    """Verify ConfigurationProvider statistics reload count tracking."""
    provider = ConfigurationProvider()
    assert provider.statistics().reload_count == 0


def test_configuration_runtime_context_delegation():
    """Verify ConfigurationRuntime context delegation."""
    runtime = ConfigurationRuntime()
    assert runtime.context().app_name == "Auralis"


def test_configuration_runtime_diagnostics_delegation():
    """Verify ConfigurationRuntime diagnostics delegation."""
    runtime = ConfigurationRuntime()
    assert runtime.diagnostics().state == ConfigurationRuntimeState.UNINITIALIZED


def test_configuration_runtime_capabilities_delegation():
    """Verify ConfigurationRuntime capabilities delegation."""
    runtime = ConfigurationRuntime()
    assert runtime.capabilities().supports_dotenv is True


def test_configuration_runtime_statistics_delegation():
    """Verify ConfigurationRuntime statistics delegation."""
    runtime = ConfigurationRuntime()
    assert runtime.statistics().active_sources_count == 3


def test_configuration_runtime_restart_state():
    """Verify ConfigurationRuntime restart transition to READY."""
    runtime = ConfigurationRuntime()
    state = runtime.restart()
    assert state == ConfigurationRuntimeState.READY


def test_lazy_singleton_accessors_thread_safety():
    """Verify lazy singleton accessors under multithreaded calls."""
    reset_configuration_runtime()
    reset_configuration_provider()

    def get_rt():
        return get_configuration_runtime()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_rt) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r is results[0] for r in results)
    reset_configuration_runtime()
    reset_configuration_provider()


def test_configuration_source_manager_has_missing_key():
    """Verify has returns False for missing key."""
    manager = ConfigurationSourceManager()
    assert manager.has("completely_absent_key_xyz") is False


def test_configuration_source_manager_get_all_empty():
    """Verify get_all when memory source is empty."""
    registry = SourceRegistry()
    mem_src = MemoryConfigurationSource(source_name="custom_empty_mem")
    registry.register_source(mem_src)
    manager = ConfigurationSourceManager(registry=registry)
    assert len(manager.get_all()) == 0


def test_configuration_source_manager_unregister_missing_source():
    """Verify unregistering missing source returns False."""
    manager = ConfigurationSourceManager()
    assert manager.unregister_source("non_existent_source") is False


def test_dotenv_source_missing_file_health():
    """Verify health reporting when .env file is missing."""
    source = DotEnvConfigurationSource(filepath="absent.env")
    assert source.health().is_healthy is True


def test_environment_source_keys_with_prefix():
    """Verify EnvironmentConfigurationSource keys method with prefix filter."""
    os.environ["PREFIX_TEST_KEY"] = "val"
    try:
        source = EnvironmentConfigurationSource(prefix="PREFIX_")
        assert "PREFIX_TEST_KEY" in source.keys()
    finally:
        del os.environ["PREFIX_TEST_KEY"]


def test_memory_source_contains_missing():
    """Verify MemoryConfigurationSource contains returns False for missing key."""
    source = MemoryConfigurationSource()
    assert source.contains("absent") is False


def test_source_registry_list_sources_order():
    """Verify SourceRegistry list_sources preserves registration order."""
    registry = SourceRegistry()
    s1 = MemoryConfigurationSource(source_name="s1", priority=100)
    s2 = MemoryConfigurationSource(source_name="s2", priority=500)
    registry.register_source(s1)
    registry.register_source(s2)

    listed = registry.list_sources()
    assert listed[0].source_name == "s1"
    assert listed[1].source_name == "s2"


def test_source_registry_get_source_missing():
    """Verify SourceRegistry get_source returns None for missing source."""
    registry = SourceRegistry()
    assert registry.get_source("missing") is None


# ============================================================================
# 9. Concurrent Multithreaded Tests
# ============================================================================


def test_concurrent_configuration_resolver():
    """Verify thread-safe parallel resolution using ConfigurationResolver."""
    resolver = ConfigurationResolver()

    def do_convert(i: int):
        return resolver.resolve_key(f"key_{i}", str(i), expected_type=int)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_convert, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert resolver.statistics().conversion_count == 50


def test_concurrent_configuration_validator():
    """Verify thread-safe parallel validation using ConfigurationValidator."""
    schema_manager = ConfigurationSchemaManager()
    defn = ConfigurationDefinition(key="count", expected_type=int, default_value=1)
    schema_manager.register_schema(ConfigurationSchema(schema_name="count_schema", definitions=(defn,)))
    validator = ConfigurationValidator(schema_manager=schema_manager)

    def do_validate(i: int):
        return validator.validate({"count": i})

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_validate, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert all(r.is_valid for r in results)
    assert validator.statistics().validation_count == 50


def test_concurrent_configuration_source_manager_resolve():
    """Verify thread-safe concurrent resolve calls on ConfigurationSourceManager."""
    manager = ConfigurationSourceManager()
    defn = ConfigurationDefinition(key="concurrent_port", expected_type=int, default_value=9090)
    manager.register_schema(ConfigurationSchema(schema_name="conc_schema", definitions=(defn,)))

    def do_resolve():
        return manager.resolve("concurrent_port")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_resolve) for _ in range(50)]
        results = [f.result() for f in futures]

    assert all(r == 9090 for r in results)
