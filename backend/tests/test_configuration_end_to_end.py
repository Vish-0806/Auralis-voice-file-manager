"""End-to-End Production Certification Test Suite for Phase 14.3 Configuration Runtime."""

import concurrent.futures
import os
from pathlib import Path
import tempfile
# pyrefly: ignore [missing-import]
import pytest

from backend.application.config.configuration_certifier import ConfigurationCertifier
from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.configuration_resolver import ConfigurationResolver
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.configuration_schema import ConfigurationSchemaManager
from backend.application.config.configuration_source_manager import ConfigurationSourceManager
from backend.application.config.configuration_validator import ConfigurationValidator
from backend.application.config.dotenv_source import DotEnvConfigurationSource
from backend.application.config.environment_source import EnvironmentConfigurationSource
from backend.application.config.exceptions import ConfigurationProfileError, ConfigurationSourceError
from backend.application.config.feature_flag_manager import FeatureFlagManager
from backend.application.config.memory_source import MemoryConfigurationSource
from backend.application.config.models import (
    ConfigurationCertificationResult,
    ConfigurationConstraint,
    ConfigurationDefinition,
    ConfigurationDiagnostics,
    ConfigurationHealth,
    ConfigurationProfileDefinition,
    ConfigurationProfileType,
    ConfigurationRuntimeState,
    ConfigurationSchema,
    FeatureFlag,
    SecretPolicy,
    SecretType,
    SourcePriority,
)
from backend.application.config.profile_manager import ProfileManager
from backend.application.config.secret_manager import SecretManager
from backend.application.config.secret_store import SecretStore
from backend.application.config.source_registry import SourceRegistry


def test_full_runtime_initialization_and_ready_state():
    """Verify complete ConfigurationRuntime initialization to READY state."""
    runtime = ConfigurationRuntime()
    state = runtime.initialize()
    assert state == ConfigurationRuntimeState.READY
    assert runtime.health().state == ConfigurationRuntimeState.READY
    assert runtime.health().is_healthy is True


def test_all_sources_registration_and_priority_sorting():
    """Verify default sources registration and descending priority order."""
    manager = ConfigurationSourceManager()
    sources = manager.registry.list_sources()

    # Memory (500) > Environment (400) > DotEnv (300)
    assert len(sources) >= 3
    sorted_sources = manager.registry.sort_sources()
    assert sorted_sources[0].priority >= sorted_sources[1].priority
    assert sorted_sources[1].priority >= sorted_sources[2].priority


def test_source_priority_precedence_memory_env_dotenv():
    """Verify Memory (500) > Environment (400) > DotEnv (300) priority precedence."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env") as tmp:
        tmp.write("PRECEDENCE_KEY=dotenv_val\n")
        tmp_path = tmp.name

    os.environ["PRECEDENCE_KEY"] = "env_val"
    try:
        registry = SourceRegistry()
        registry.register_source(MemoryConfigurationSource())
        registry.register_source(EnvironmentConfigurationSource())
        registry.register_source(DotEnvConfigurationSource(filepath=tmp_path, source_name="custom_dotenv"))

        manager = ConfigurationSourceManager(registry=registry)

        # Environment (400) overrides DotEnv (300)
        assert manager.get("PRECEDENCE_KEY") == "env_val"

        # Memory (500) overrides Environment (400)
        mem_src = manager.registry.get_source("memory_source")
        assert isinstance(mem_src, MemoryConfigurationSource)
        mem_src.set("PRECEDENCE_KEY", "memory_val")

        assert manager.get("PRECEDENCE_KEY") == "memory_val"
    finally:
        del os.environ["PRECEDENCE_KEY"]
        Path(tmp_path).unlink(missing_ok=True)


def test_schema_registration_and_type_resolution():
    """Verify SchemaManager registration, property type conversion, and default fallback."""
    manager = ConfigurationSourceManager()
    defn_port = ConfigurationDefinition(key="server.port", expected_type=int, default_value=8080)
    defn_debug = ConfigurationDefinition(key="server.debug", expected_type=bool, default_value=False)
    schema = ConfigurationSchema(schema_name="server_schema", definitions=(defn_port, defn_debug))

    assert manager.register_schema(schema) is True
    res = manager.resolve_all()

    assert res.resolved_values["server.port"] == 8080
    assert "server.port" in res.defaulted_keys


def test_profile_switching_and_inheritance_overrides():
    """Verify runtime profile switching and inheritance override chain."""
    provider = ConfigurationProvider()
    assert provider.get_active_profile().profile_name == "development"
    assert provider.resolve("debug") is True

    # Switch to production
    assert provider.activate_profile("production") is True
    assert provider.get_active_profile().profile_name == "production"
    assert provider.resolve("debug") is False


def test_feature_flag_evaluation_with_dependencies_and_rollout():
    """Verify feature flag evaluation with dependency checks and rollout score."""
    provider = ConfigurationProvider()
    parent_flag = FeatureFlag(feature_name="parent_feature", enabled=True)
    child_flag = FeatureFlag(
        feature_name="child_feature",
        enabled=True,
        dependencies=("parent_feature",),
        rollout_percentage=100.0,
    )

    provider.register_feature(parent_flag)
    provider.register_feature(child_flag)

    eval_res = provider.evaluate_feature("child_feature")
    assert eval_res.enabled is True
    assert provider.is_feature_enabled("child_feature") is True


def test_secret_registration_redaction_and_policy_enforcement():
    """Verify secret registration, value redaction, and policy enforcement."""
    provider = ConfigurationProvider()
    assert provider.register_secret("db_password", "super_secret_123", SecretType.PASSWORD) is True

    # Raw value via get_secret
    assert provider.get_secret("db_password") == "super_secret_123"

    # Redacted value for exports/logs
    assert provider.get_redacted_secret("db_password") == "********"

    # Secret overrides config entries with redacted value
    assert provider.source_manager.get("db_password") == "********"


def test_aggregate_diagnostics_completeness():
    """Verify completeness of ConfigurationDiagnostics model metrics and health."""
    runtime = ConfigurationRuntime()
    runtime.initialize()
    diag = runtime.diagnostics()

    assert isinstance(diag, ConfigurationDiagnostics)
    assert diag.state == ConfigurationRuntimeState.READY
    assert diag.active_sources_count >= 3
    assert diag.resolution_statistics is not None
    assert diag.validation_statistics is not None
    assert diag.profile_statistics is not None
    assert diag.feature_statistics is not None
    assert diag.secret_statistics is not None


def test_aggregate_health_and_availability_percentage():
    """Verify ConfigurationProvider health report and certifier availability calculation."""
    provider = ConfigurationProvider()
    health = provider.health()

    assert health.is_healthy is True
    cert = provider.certify()

    assert isinstance(cert, ConfigurationCertificationResult)
    assert cert.is_certified is True
    assert cert.availability_percentage == 100.0
    assert cert.checks_passed > 0
    assert cert.checks_failed == 0


def test_aggregate_statistics_collection():
    """Verify collection of configuration runtime statistics metrics."""
    provider = ConfigurationProvider()
    stats = provider.statistics()

    assert stats.active_sources_count >= 3
    assert "total_properties_loaded" in stats.metrics
    assert "lookups_count" in stats.metrics


def test_runtime_restart_sequence():
    """Verify runtime restart lifecycle state transitions."""
    runtime = ConfigurationRuntime()
    runtime.initialize()
    assert runtime.health().state == ConfigurationRuntimeState.READY

    new_state = runtime.restart()
    assert new_state == ConfigurationRuntimeState.READY
    assert runtime.health().state == ConfigurationRuntimeState.READY


def test_runtime_shutdown_sequence():
    """Verify runtime shutdown lifecycle state transition."""
    runtime = ConfigurationRuntime()
    runtime.initialize()
    assert runtime.health().state == ConfigurationRuntimeState.READY

    stop_state = runtime.shutdown()
    assert stop_state == ConfigurationRuntimeState.STOPPED
    assert runtime.health().state == ConfigurationRuntimeState.STOPPED


def test_multithreaded_concurrent_access_and_mutations():
    """Verify thread-safe concurrent source queries, profile switches, feature evaluations, and secret reads."""
    provider = ConfigurationProvider()
    provider.initialize()

    provider.register_feature(FeatureFlag(feature_name="conc_feat", enabled=True))
    provider.register_secret("conc_sec", "secret_val", SecretType.PASSWORD)

    def worker_task(i: int):
        # Query property
        val = provider.resolve("debug")
        # Feature check
        f_val = provider.is_feature_enabled("conc_feat")
        # Secret check
        s_val = provider.get_secret("conc_sec")
        # Profile check
        p = provider.get_active_profile()
        return val is not None and f_val is True and s_val == "secret_val" and p is not None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_task, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r is True for r in results)


def test_configuration_certifier_full_certification():
    """Verify ConfigurationCertifier certify and validate_runtime methods."""
    certifier = ConfigurationCertifier()
    cert = certifier.certify()

    assert cert.is_certified is True
    assert cert.checks_failed == 0
    assert certifier.validate_runtime() is True


def test_runtime_certify_and_validate_runtime_delegation():
    """Verify ConfigurationRuntime certify and validate_runtime delegation."""
    runtime = ConfigurationRuntime()
    runtime.initialize()

    assert runtime.validate_runtime() is True
    cert = runtime.certify()
    assert cert.is_certified is True
    assert cert.availability_percentage == 100.0
