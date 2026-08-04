"""Comprehensive unit tests for Phase 14.3.2 Configuration Source Management & Runtime Foundation."""

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
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.configuration_source_manager import ConfigurationSourceManager
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
    ConfigurationContext,
    ConfigurationDiagnostics,
    ConfigurationEntry,
    ConfigurationHealth,
    ConfigurationProfile,
    ConfigurationProfileType,
    ConfigurationRuntimeState,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationSourceType,
    ConfigurationState,
    ConfigurationStatistics,
    SourceHealth,
    SourcePriority,
    SourceRegistration,
    SourceStatistics,
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


def test_configuration_source_model():
    """Verify ConfigurationSource model."""
    source = ConfigurationSource(source_type=ConfigurationSourceType.JSON, source_name="app_config")
    assert source.source_type == ConfigurationSourceType.JSON
    assert source.source_name == "app_config"


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
# 4. Configuration Source Implementation Tests (Phase 14.3.2)
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


def test_memory_configuration_source_statistics_and_health():
    """Verify MemoryConfigurationSource health and statistics metrics."""
    source = MemoryConfigurationSource()
    source.set("key1", "val1")

    assert source.get("key1") == "val1"
    assert source.get("missing_key") is None

    stats = source.statistics()
    assert stats.hits_count == 1
    assert stats.misses_count == 1
    assert source.health().is_healthy is True


def test_environment_configuration_source_reads():
    """Verify EnvironmentConfigurationSource reads from os.environ."""
    os.environ["AURALIS_TEST_ENV_KEY"] = "env_value_123"
    try:
        source = EnvironmentConfigurationSource()
        assert source.contains("AURALIS_TEST_ENV_KEY") is True
        assert source.get("AURALIS_TEST_ENV_KEY") == "env_value_123"
    finally:
        del os.environ["AURALIS_TEST_ENV_KEY"]


def test_environment_configuration_source_prefix():
    """Verify EnvironmentConfigurationSource with custom prefix."""
    os.environ["AURALIS_PORT"] = "8080"
    try:
        source = EnvironmentConfigurationSource(prefix="AURALIS_")
        assert source.get("PORT") == "8080"
    finally:
        del os.environ["AURALIS_PORT"]


def test_dotenv_configuration_source_file_reading():
    """Verify DotEnvConfigurationSource reads from a temporary .env file."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env") as tmp:
        tmp.write("DB_HOST=localhost\nDB_PORT=5432\n# Comment line\n")
        tmp_path = tmp.name

    try:
        source = DotEnvConfigurationSource(filepath=tmp_path)
        assert source.contains("DB_HOST") is True
        assert source.get("DB_HOST") == "localhost"
        assert source.get("DB_PORT") == "5432"
        assert source.get("MISSING") is None
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ============================================================================
# 5. SourceRegistry Component Tests (Phase 14.3.2)
# ============================================================================


def test_source_registry_registration_and_priority_sorting():
    """Verify SourceRegistry registering and sorting sources by priority descending."""
    registry = SourceRegistry()
    src_dotenv = DotEnvConfigurationSource(priority=300)
    src_memory = MemoryConfigurationSource(priority=500)
    src_env = EnvironmentConfigurationSource(priority=400)

    registry.register_source(src_dotenv)
    registry.register_source(src_memory)
    registry.register_source(src_env)

    assert registry.count() == 3

    sorted_sources = registry.sort_sources()
    assert sorted_sources[0].priority == 500  # Memory
    assert sorted_sources[1].priority == 400  # Environment
    assert sorted_sources[2].priority == 300  # DotEnv


def test_source_registry_duplicate_registration_raises():
    """Verify registering duplicate source_name raises ConfigurationSourceError."""
    registry = SourceRegistry()
    src1 = MemoryConfigurationSource(source_name="memory_1")
    src2 = MemoryConfigurationSource(source_name="memory_1")

    registry.register_source(src1)
    with pytest.raises(ConfigurationSourceError):
        registry.register_source(src2)


def test_source_registry_unregister_and_contains():
    """Verify SourceRegistry unregister_source and contains methods."""
    registry = SourceRegistry()
    src = MemoryConfigurationSource(source_name="mem_temp")
    registry.register_source(src)

    assert registry.contains("mem_temp") is True
    assert registry.unregister_source("mem_temp") is True
    assert registry.contains("mem_temp") is False
    assert registry.unregister_source("non_existent") is False


# ============================================================================
# 6. ConfigurationSourceManager Tests (Phase 14.3.2)
# ============================================================================


def test_configuration_source_manager_priority_resolution():
    """Verify ConfigurationSourceManager priority resolution (Memory > Environment > DotEnv)."""
    registry = SourceRegistry()

    mem_source = MemoryConfigurationSource(initial_values={"shared_key": "memory_value"})
    env_source = EnvironmentConfigurationSource()
    os.environ["shared_key"] = "env_value"

    try:
        registry.register_source(mem_source)
        registry.register_source(env_source)

        manager = ConfigurationSourceManager(registry=registry)

        # Memory (500) overrides Environment (400)
        assert manager.get("shared_key") == "memory_value"

        # Remove from memory -> falls back to Environment
        mem_source.remove("shared_key")
        assert manager.get("shared_key") == "env_value"
    finally:
        if "shared_key" in os.environ:
            del os.environ["shared_key"]


def test_configuration_source_manager_get_entry():
    """Verify ConfigurationSourceManager get_entry returns ConfigurationEntry model with metadata."""
    manager = ConfigurationSourceManager()
    mem_src = manager.registry.get_source("memory_source")
    assert isinstance(mem_src, MemoryConfigurationSource)
    mem_src.set("test_key", "test_val")

    entry = manager.get_entry("test_key")
    assert entry is not None
    assert entry.key == "test_key"
    assert entry.value == "test_val"
    assert entry.source_type == ConfigurationSourceType.MEMORY
    assert entry.priority == 500


def test_configuration_source_manager_get_all_merged():
    """Verify get_all merges properties starting from lowest to highest priority."""
    registry = SourceRegistry()
    src_low = MemoryConfigurationSource(source_name="low", priority=100, initial_values={"a": 1, "b": 2})
    src_high = MemoryConfigurationSource(source_name="high", priority=500, initial_values={"b": 99, "c": 3})

    registry.register_source(src_low)
    registry.register_source(src_high)

    manager = ConfigurationSourceManager(registry=registry)
    merged = manager.get_all()

    assert merged["a"] == 1
    assert merged["b"] == 99  # High priority wins
    assert merged["c"] == 3


def test_configuration_source_manager_create_snapshot():
    """Verify ConfigurationSourceManager create_snapshot snapshot generation."""
    manager = ConfigurationSourceManager()
    snapshot = manager.create_snapshot()

    assert isinstance(snapshot, ConfigurationSnapshot)
    assert isinstance(snapshot.values, dict)
    assert len(snapshot.sources_metadata) == 3


def test_configuration_source_manager_has_key():
    """Verify ConfigurationSourceManager has(key) method."""
    manager = ConfigurationSourceManager()
    mem_src = manager.registry.get_source("memory_source")
    assert isinstance(mem_src, MemoryConfigurationSource)
    mem_src.set("present_key", "val")

    assert manager.has("present_key") is True
    assert manager.has("missing_key") is False


# ============================================================================
# 7. ConfigurationProvider & ConfigurationRuntime Tests
# ============================================================================


def test_configuration_provider_initialization_and_shutdown():
    """Verify ConfigurationProvider lifecycle state transitions."""
    provider = ConfigurationProvider()
    assert provider.health().state == ConfigurationRuntimeState.UNINITIALIZED

    state_ready = provider.initialize()
    assert state_ready == ConfigurationRuntimeState.READY
    assert provider.health().is_healthy is True

    state_stopped = provider.shutdown()
    assert state_stopped == ConfigurationRuntimeState.STOPPED


def test_configuration_provider_restart():
    """Verify ConfigurationProvider restart functionality."""
    provider = ConfigurationProvider()
    provider.initialize()
    restart_state = provider.restart()
    assert restart_state == ConfigurationRuntimeState.READY


def test_configuration_provider_health_reporting():
    """Verify ConfigurationProvider health reporting."""
    provider = ConfigurationProvider()
    assert provider.health().is_healthy is True

    provider.initialize()
    assert provider.health().is_healthy is True

    provider.shutdown()
    assert provider.health().is_healthy is False
    assert provider.health().state == ConfigurationRuntimeState.STOPPED


def test_configuration_provider_statistics():
    """Verify ConfigurationProvider statistics metric snapshot."""
    provider = ConfigurationProvider()
    stats = provider.statistics()
    assert isinstance(stats, ConfigurationStatistics)
    assert "reload_count" in stats.metrics


def test_configuration_provider_capabilities():
    """Verify ConfigurationProvider capabilities declarations."""
    provider = ConfigurationProvider()
    caps = provider.capabilities()
    assert isinstance(caps, ConfigurationCapabilities)
    assert caps.supports_dotenv is True


def test_configuration_provider_diagnostics():
    """Verify ConfigurationProvider diagnostics model generation."""
    provider = ConfigurationProvider()
    diag = provider.diagnostics()
    assert isinstance(diag, ConfigurationDiagnostics)
    assert diag.active_profile_name == "development"


def test_configuration_provider_get_context():
    """Verify ConfigurationProvider get_context snapshot."""
    context = ConfigurationContext(app_name="CustomApp", environment=ConfigurationProfileType.STAGING)
    provider = ConfigurationProvider(config_context=context)

    ctx = provider.get_context()
    assert ctx.app_name == "CustomApp"
    assert ctx.environment == ConfigurationProfileType.STAGING


def test_configuration_runtime_lifecycle():
    """Verify ConfigurationRuntime lifecycle transitions."""
    runtime = ConfigurationRuntime()
    assert runtime.health().state == ConfigurationRuntimeState.UNINITIALIZED

    ready_state = runtime.initialize()
    assert ready_state == ConfigurationRuntimeState.READY
    assert runtime.health().is_healthy is True

    restart_state = runtime.restart()
    assert restart_state == ConfigurationRuntimeState.READY

    stopped_state = runtime.shutdown()
    assert stopped_state == ConfigurationRuntimeState.STOPPED


def test_configuration_runtime_delegation():
    """Verify ConfigurationRuntime delegation of health, statistics, capabilities, diagnostics, context."""
    provider = ConfigurationProvider()
    runtime = ConfigurationRuntime(provider=provider)

    assert runtime.health().is_healthy is True
    assert isinstance(runtime.statistics(), ConfigurationStatistics)
    assert isinstance(runtime.capabilities(), ConfigurationCapabilities)
    assert isinstance(runtime.diagnostics(), ConfigurationDiagnostics)
    assert isinstance(runtime.context(), ConfigurationContext)


def test_constructor_dependency_injection_provider():
    """Verify ConfigurationRuntime constructor accepts custom provider."""
    custom_context = ConfigurationContext(app_name="InjectedApp")
    custom_provider = ConfigurationProvider(config_context=custom_context)
    runtime = ConfigurationRuntime(provider=custom_provider)

    assert runtime.context().app_name == "InjectedApp"
    assert runtime.provider is custom_provider


# ============================================================================
# 8. Runtime Lazy Singleton Accessors Tests
# ============================================================================


def test_configuration_runtime_lazy_singletons():
    """Verify get_configuration_runtime, set_configuration_runtime, reset_configuration_runtime."""
    reset_configuration_runtime()
    reset_configuration_provider()

    runtime = get_configuration_runtime()
    assert isinstance(runtime, IConfigurationRuntime)

    custom_runtime = ConfigurationRuntime()
    set_configuration_runtime(custom_runtime)
    assert get_configuration_runtime() is custom_runtime

    reset_configuration_runtime()
    reset_configuration_provider()


def test_configuration_provider_lazy_singletons():
    """Verify get_configuration_provider, set_configuration_provider, reset_configuration_provider."""
    reset_configuration_runtime()
    reset_configuration_provider()

    provider = get_configuration_provider()
    assert isinstance(provider, IConfigurationProvider)

    custom_provider = ConfigurationProvider()
    set_configuration_provider(custom_provider)
    assert get_configuration_provider() is custom_provider

    reset_configuration_runtime()
    reset_configuration_provider()


# ============================================================================
# 9. Concurrent Multithreaded Tests
# ============================================================================


def test_concurrent_memory_source_reads_and_writes():
    """Verify thread-safe concurrent reads and writes on MemoryConfigurationSource."""
    source = MemoryConfigurationSource()

    def do_write(i: int):
        source.set(f"key_{i}", i)

    def do_read(i: int):
        return source.get(f"key_{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        write_futures = [executor.submit(do_write, i) for i in range(50)]
        concurrent.futures.wait(write_futures)

        read_futures = [executor.submit(do_read, i) for i in range(50)]
        results = [f.result() for f in read_futures]

    assert len(results) == 50
    assert source.statistics().total_keys == 50


def test_concurrent_source_manager_lookups():
    """Verify thread-safe parallel lookups on ConfigurationSourceManager."""
    manager = ConfigurationSourceManager()
    mem_src = manager.registry.get_source("memory_source")
    assert isinstance(mem_src, MemoryConfigurationSource)
    mem_src.set("shared_concurrent_key", "value_123")

    def do_lookup():
        return manager.get("shared_concurrent_key")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(do_lookup) for _ in range(50)]
        results = [f.result() for f in futures]

    assert all(r == "value_123" for r in results)


def test_dotenv_configuration_source_health_and_stats():
    """Verify DotEnvConfigurationSource health and statistics methods."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env") as tmp:
        tmp.write("KEY_A=VAL_A\nKEY_B=VAL_B\n")
        tmp_path = tmp.name

    try:
        source = DotEnvConfigurationSource(filepath=tmp_path)
        assert source.health().is_healthy is True
        assert source.statistics().total_keys == 2
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_dotenv_configuration_source_non_existent_file():
    """Verify DotEnvConfigurationSource handles non-existent file path gracefully."""
    source = DotEnvConfigurationSource(filepath="non_existent_file.env")
    assert source.contains("ANY_KEY") is False
    assert source.get("ANY_KEY") is None
    assert source.statistics().total_keys == 0


def test_environment_configuration_source_statistics():
    """Verify EnvironmentConfigurationSource statistics and health."""
    source = EnvironmentConfigurationSource()
    assert source.health().is_healthy is True
    assert source.statistics().total_keys == len(os.environ)


def test_memory_configuration_source_items():
    """Verify MemoryConfigurationSource items method returns tuple of pairs."""
    source = MemoryConfigurationSource(initial_values={"k1": "v1", "k2": "v2"})
    items = source.items()
    assert len(items) == 2
    assert ("k1", "v1") in items
    assert ("k2", "v2") in items


def test_source_registry_clear():
    """Verify SourceRegistry clear method empties all registered sources."""
    registry = SourceRegistry()
    registry.register_source(MemoryConfigurationSource())
    assert registry.count() == 1

    registry.clear()
    assert registry.count() == 0


def test_configuration_source_manager_unregister_source():
    """Verify unregistering a source from ConfigurationSourceManager."""
    manager = ConfigurationSourceManager()
    assert manager.registry.contains("memory_source") is True

    assert manager.unregister_source("memory_source") is True
    assert manager.registry.contains("memory_source") is False


def test_configuration_source_manager_diagnostics_timestamp():
    """Verify ConfigurationSourceManager diagnostics timestamp validity."""
    manager = ConfigurationSourceManager()
    diag = manager.diagnostics()
    assert diag.timestamp is not None
    assert diag.active_sources_count == 3


def test_configuration_source_manager_get_default():
    """Verify get fallback to default value when missing across all sources."""
    manager = ConfigurationSourceManager()
    assert manager.get("non_existent_global_key", default="fallback_val") == "fallback_val"


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
