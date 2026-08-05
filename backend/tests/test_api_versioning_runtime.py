"""Tests for API Versioning & Documentation Runtime (Phase 15.6).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
version registry, compatibility manager, documentation manager, provider lifecycle,
runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
import json

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
from pydantic import ValidationError as PydanticValidationError

from backend.application.api.versioning import (
    ApiRelease,
    ApiVersion,
    CompatibilityException,
    CompatibilityManager,
    CompatibilityReport,
    DeprecationException,
    DeprecationNotice,
    DeprecationState,
    DocumentationException,
    DocumentationExport,
    DocumentationManager,
    DocumentationPage,
    DocumentationSection,
    EndpointVersion,
    ICompatibilityManager,
    IDocumentationManager,
    IVersionRegistry,
    IVersioningProvider,
    IVersioningRuntime,
    ReleaseChannel,
    VersionCapabilities,
    VersionDiagnostics,
    VersionHealth,
    VersionRegistrationException,
    VersionRegistry,
    VersionRuntimeState,
    VersionStatistics,
    VersioningException,
    VersioningProvider,
    VersioningRuntime,
    get_versioning_provider,
    get_versioning_runtime,
    reset_versioning_provider,
    reset_versioning_runtime,
    set_versioning_provider,
    set_versioning_runtime,
)


@pytest.fixture(autouse=True)
def _reset_versioning_singletons():
    """Reset versioning singletons before and after each test."""
    reset_versioning_runtime()
    reset_versioning_provider()
    yield
    reset_versioning_runtime()
    reset_versioning_provider()


# --- Enum Tests ---

def test_enum_release_channel():
    """Verify ReleaseChannel enum values."""
    assert ReleaseChannel.ALPHA.value == "ALPHA"
    assert ReleaseChannel.BETA.value == "BETA"
    assert ReleaseChannel.RC.value == "RC"
    assert ReleaseChannel.STABLE.value == "STABLE"
    assert ReleaseChannel.LTS.value == "LTS"
    assert len(ReleaseChannel) == 5


def test_enum_deprecation_state():
    """Verify DeprecationState enum values."""
    assert DeprecationState.ACTIVE.value == "ACTIVE"
    assert DeprecationState.DEPRECATED.value == "DEPRECATED"
    assert DeprecationState.REMOVED.value == "REMOVED"
    assert len(DeprecationState) == 3


def test_enum_version_runtime_state():
    """Verify VersionRuntimeState enum values."""
    assert VersionRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert VersionRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert VersionRuntimeState.READY.value == "READY"
    assert VersionRuntimeState.STOPPING.value == "STOPPING"
    assert VersionRuntimeState.STOPPED.value == "STOPPED"
    assert len(VersionRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_deprecation_notice():
    """Verify DeprecationNotice defaults and immutability."""
    notice = DeprecationNotice(notice_id="n1", deprecated_version="1.0.0", reason="Obsolete")
    assert notice.notice_id == "n1"
    assert notice.state == DeprecationState.DEPRECATED

    with pytest.raises((PydanticValidationError, TypeError)):
        notice.reason = "NewReason"  # type: ignore[attr-defined]


def test_model_immutability_endpoint_version():
    """Verify EndpointVersion defaults and immutability."""
    ep = EndpointVersion(endpoint_id="e1", path="/files", version="1.0.0")
    assert ep.endpoint_id == "e1"
    assert ep.state == DeprecationState.ACTIVE

    with pytest.raises((PydanticValidationError, TypeError)):
        ep.path = "/new_files"  # type: ignore[attr-defined]


def test_model_immutability_api_release():
    """Verify ApiRelease defaults and immutability."""
    rel = ApiRelease(release_id="r1", version="1.0.0", channel=ReleaseChannel.STABLE)
    assert rel.release_id == "r1"

    with pytest.raises((PydanticValidationError, TypeError)):
        rel.channel = ReleaseChannel.BETA  # type: ignore[attr-defined]


def test_model_immutability_api_version():
    """Verify ApiVersion defaults and immutability."""
    ver = ApiVersion(version_id="v1", version_number="1.0.0")
    assert ver.version_id == "v1"
    assert ver.channel == ReleaseChannel.STABLE

    with pytest.raises((PydanticValidationError, TypeError)):
        ver.version_number = "2.0.0"  # type: ignore[attr-defined]


def test_model_immutability_compatibility_report():
    """Verify CompatibilityReport defaults and immutability."""
    rep = CompatibilityReport(is_compatible=True, base_version="1.0.0", target_version="1.1.0")
    assert rep.is_compatible is True

    with pytest.raises((PydanticValidationError, TypeError)):
        rep.is_compatible = False  # type: ignore[attr-defined]


def test_model_immutability_documentation_section():
    """Verify DocumentationSection defaults and immutability."""
    sec = DocumentationSection(section_id="sec1", title="Overview")
    assert sec.section_id == "sec1"

    with pytest.raises((PydanticValidationError, TypeError)):
        sec.title = "NewTitle"  # type: ignore[attr-defined]


def test_model_immutability_documentation_page():
    """Verify DocumentationPage defaults and immutability."""
    page = DocumentationPage(page_id="p1", title="User Guide")
    assert page.page_id == "p1"

    with pytest.raises((PydanticValidationError, TypeError)):
        page.title = "Developer Guide"  # type: ignore[attr-defined]


def test_model_immutability_documentation_export():
    """Verify DocumentationExport defaults and immutability."""
    exp = DocumentationExport(export_id="exp1", format="markdown", content="# Header")
    assert exp.export_id == "exp1"

    with pytest.raises((PydanticValidationError, TypeError)):
        exp.format = "json"  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify VersionCapabilities defaults and immutability."""
    caps = VersionCapabilities()
    assert caps.supports_version_registration is True

    with pytest.raises((PydanticValidationError, TypeError)):
        caps.supports_version_registration = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify VersionStatistics defaults and immutability."""
    stats = VersionStatistics()
    assert stats.total_versions == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        stats.total_versions = 5  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify VersionHealth defaults and immutability."""
    health = VersionHealth()
    assert health.is_healthy is True

    with pytest.raises((PydanticValidationError, TypeError)):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify VersionDiagnostics defaults and immutability."""
    diag = VersionDiagnostics()
    assert diag.registered_versions_count == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        diag.registered_versions_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(VersionRegistrationException, VersioningException)
    assert issubclass(CompatibilityException, VersioningException)
    assert issubclass(DocumentationException, VersioningException)
    assert issubclass(DeprecationException, VersioningException)
    assert issubclass(VersioningException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        IVersionRegistry()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        ICompatibilityManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IDocumentationManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IVersioningProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IVersioningRuntime()  # type: ignore[abstract]


# --- VersionRegistry Tests ---

def test_registry_register_and_lookup():
    """Verify registering and looking up ApiVersion."""
    registry = VersionRegistry()
    ver = ApiVersion(version_id="v1", version_number="1.0.0")
    registered = registry.register_version(ver)

    assert registered.version_id == "v1"
    assert registry.lookup_version("v1") == ver
    assert registry.count_versions() == 1


def test_registry_lookup_by_version_number():
    """Verify lookup by version number string."""
    registry = VersionRegistry()
    ver = ApiVersion(version_id="v1", version_number="1.0.0")
    registry.register_version(ver)

    assert registry.lookup_version("1.0.0") == ver


def test_registry_duplicate_version_id_exception():
    """Verify VersionRegistrationException on duplicate version ID."""
    registry = VersionRegistry()
    v1 = ApiVersion(version_id="v1", version_number="1.0.0")
    v2 = ApiVersion(version_id="v1", version_number="1.1.0")

    registry.register_version(v1)
    with pytest.raises(VersionRegistrationException):
        registry.register_version(v2)


def test_registry_duplicate_version_number_exception():
    """Verify VersionRegistrationException on duplicate version number."""
    registry = VersionRegistry()
    v1 = ApiVersion(version_id="v1", version_number="1.0.0")
    v2 = ApiVersion(version_id="v2", version_number="1.0.0")

    registry.register_version(v1)
    with pytest.raises(VersionRegistrationException):
        registry.register_version(v2)


def test_registry_unregister():
    """Verify unregistering an API version."""
    registry = VersionRegistry()
    ver = ApiVersion(version_id="v1", version_number="1.0.0")
    registry.register_version(ver)

    removed = registry.unregister_version("v1")
    assert removed == ver
    assert registry.lookup_version("v1") is None
    assert registry.count_versions() == 0


def test_registry_get_latest_version():
    """Verify get_latest_version resolving highest semver."""
    registry = VersionRegistry()
    registry.register_version(ApiVersion(version_id="v1", version_number="1.0.0"))
    registry.register_version(ApiVersion(version_id="v3", version_number="2.1.0"))
    registry.register_version(ApiVersion(version_id="v2", version_number="2.0.0"))

    latest = registry.get_latest_version()
    assert latest is not None
    assert latest.version_number == "2.1.0"


def test_registry_get_latest_version_with_channel_filter():
    """Verify get_latest_version filtering by release channel."""
    registry = VersionRegistry()
    registry.register_version(ApiVersion(version_id="v1", version_number="1.0.0", channel=ReleaseChannel.STABLE))
    registry.register_version(ApiVersion(version_id="v2", version_number="3.0.0", channel=ReleaseChannel.ALPHA))

    latest_stable = registry.get_latest_version(channel=ReleaseChannel.STABLE)
    assert latest_stable is not None
    assert latest_stable.version_number == "1.0.0"


def test_registry_list_and_count():
    """Verify list_versions and count_versions."""
    registry = VersionRegistry()
    registry.register_version(ApiVersion(version_id="v1", version_number="1.0.0"))
    registry.register_version(ApiVersion(version_id="v2", version_number="1.1.0"))

    assert registry.count_versions() == 2
    assert len(registry.list_versions()) == 2


def test_registry_clear():
    """Verify clearing all registered versions."""
    registry = VersionRegistry()
    registry.register_version(ApiVersion(version_id="v1", version_number="1.0.0"))
    registry.clear()

    assert registry.count_versions() == 0


# --- CompatibilityManager Tests ---

def test_compatibility_evaluate_same_version():
    """Verify compatibility evaluation for identical version numbers."""
    mgr = CompatibilityManager()
    report = mgr.evaluate_version_strings("1.0.0", "1.0.0")

    assert report.is_compatible is True
    assert len(report.breaking_changes) == 0


def test_compatibility_evaluate_minor_upgrade():
    """Verify minor version upgrade compatibility."""
    mgr = CompatibilityManager()
    report = mgr.evaluate_version_strings("1.0.0", "1.2.0")

    assert report.is_compatible is True
    assert len(report.breaking_changes) == 0


def test_compatibility_evaluate_major_breaking_change():
    """Verify major version upgrade breaking change detection."""
    mgr = CompatibilityManager()
    report = mgr.evaluate_version_strings("1.0.0", "2.0.0")

    assert report.is_compatible is False
    assert len(report.breaking_changes) == 1
    assert "breaking changes" in report.breaking_changes[0]


def test_compatibility_evaluate_major_downgrade():
    """Verify major version downgrade incompatibility."""
    mgr = CompatibilityManager()
    report = mgr.evaluate_version_strings("2.0.0", "1.0.0")

    assert report.is_compatible is False
    assert len(report.breaking_changes) == 1


def test_compatibility_evaluate_deprecation_warnings():
    """Verify deprecation warnings during version evaluation."""
    mgr = CompatibilityManager()
    notice = DeprecationNotice(notice_id="n1", deprecated_version="1.0.0", reason="Old API")
    v1 = ApiVersion(version_id="v1", version_number="1.0.0", state=DeprecationState.DEPRECATED, deprecation_notice=notice)
    v2 = ApiVersion(version_id="v2", version_number="1.1.0")

    report = mgr.evaluate_compatibility(v1, v2)
    assert report.is_compatible is True
    assert len(report.warnings) >= 1


def test_compatibility_semver_parsing_edge_cases():
    """Verify semver parsing with 'v' prefix and missing components."""
    mgr = CompatibilityManager()
    report = mgr.evaluate_version_strings("v1.0", "v1.1")
    assert report.is_compatible is True


# --- DocumentationManager Tests ---

def test_documentation_manager_add_and_get_page():
    """Verify adding and retrieving a DocumentationPage."""
    mgr = DocumentationManager()
    page = DocumentationPage(page_id="p1", title="Getting Started")
    added = mgr.add_page(page)

    assert added.page_id == "p1"
    assert mgr.get_page("p1") == page
    assert mgr.count_pages() == 1


def test_documentation_manager_remove_page():
    """Verify removing a documentation page."""
    mgr = DocumentationManager()
    page = DocumentationPage(page_id="p1", title="Getting Started")
    mgr.add_page(page)

    removed = mgr.remove_page("p1")
    assert removed == page
    assert mgr.get_page("p1") is None
    assert mgr.count_pages() == 0


def test_documentation_manager_export_markdown():
    """Verify exporting documentation to Markdown."""
    mgr = DocumentationManager()
    sec = DocumentationSection(section_id="sec1", title="Introduction", content="Welcome to the API.")
    page = DocumentationPage(page_id="p1", title="Overview", sections=(sec,))
    mgr.add_page(page)

    export = mgr.export_markdown()
    assert export.format == "markdown"
    assert "# API Documentation Archive" in export.content
    assert "## Overview" in export.content
    assert "### Introduction" in export.content
    assert "Welcome to the API." in export.content


def test_documentation_manager_export_json():
    """Verify exporting documentation to JSON."""
    mgr = DocumentationManager()
    page = DocumentationPage(page_id="p1", title="Overview")
    mgr.add_page(page)

    export = mgr.export_json()
    assert export.format == "json"
    data = json.loads(export.content)
    assert "documentation_pages" in data
    assert len(data["documentation_pages"]) == 1


def test_documentation_manager_clear():
    """Verify clearing documentation manager."""
    mgr = DocumentationManager()
    mgr.add_page(DocumentationPage(page_id="p1", title="P1"))
    mgr.clear()

    assert mgr.count_pages() == 0


# --- VersioningProvider Tests ---

def test_provider_lifecycle():
    """Verify VersioningProvider initialize and shutdown transitions."""
    provider = VersioningProvider()
    assert provider.health().state == VersionRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == VersionRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == VersionRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify VersioningProvider restart cycle."""
    provider = VersioningProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == VersionRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    registry = VersionRegistry()
    registry.register_version(ApiVersion(version_id="v1", version_number="1.0.0"))

    provider = VersioningProvider(version_registry=registry)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_versions == 1
    assert provider.capabilities().supports_compatibility_evaluation is True
    assert provider.diagnostics().registered_versions_count == 1


# --- VersioningRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify VersioningRuntime delegates lifecycle calls to provider."""
    runtime = VersioningRuntime()
    assert runtime.health().state == VersionRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == VersionRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == VersionRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in VersioningProvider and VersioningRuntime."""
    registry = VersionRegistry()
    compat_mgr = CompatibilityManager()
    doc_mgr = DocumentationManager()

    provider = VersioningProvider(
        version_registry=registry,
        compatibility_manager=compat_mgr,
        documentation_manager=doc_mgr,
    )
    runtime = VersioningRuntime(provider=provider)

    assert runtime.get_provider().get_version_registry() is registry
    assert runtime.get_provider().get_compatibility_manager() is compat_mgr
    assert runtime.get_provider().get_documentation_manager() is doc_mgr


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_versioning_runtime():
    """Verify get_versioning_runtime, set_versioning_runtime, and reset_versioning_runtime."""
    r1 = get_versioning_runtime()
    r2 = get_versioning_runtime()
    assert r1 is r2
    assert isinstance(r1, VersioningRuntime)

    custom = VersioningRuntime()
    set_versioning_runtime(custom)
    assert get_versioning_runtime() is custom

    reset_versioning_runtime()
    r3 = get_versioning_runtime()
    assert r3 is not custom


def test_lazy_singleton_versioning_provider():
    """Verify get_versioning_provider, set_versioning_provider, and reset_versioning_provider."""
    p1 = get_versioning_provider()
    p2 = get_versioning_provider()
    assert p1 is p2
    assert isinstance(p1, VersioningProvider)

    custom = VersioningProvider()
    set_versioning_provider(custom)
    assert get_versioning_provider() is custom

    reset_versioning_provider()
    p3 = get_versioning_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_version_registration():
    """Verify thread-safety of VersionRegistry under concurrent registrations."""
    registry = VersionRegistry()

    def register_worker(idx: int):
        registry.register_version(ApiVersion(version_id=f"v_{idx}", version_number=f"1.0.{idx}"))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert registry.count_versions() == 40


def test_concurrent_compatibility_evaluations():
    """Verify thread-safety of CompatibilityManager under concurrent evaluations."""
    mgr = CompatibilityManager()

    def eval_worker(idx: int):
        return mgr.evaluate_version_strings(f"1.0.{idx}", f"2.0.{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(eval_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.is_compatible is False for r in results)


def test_concurrent_documentation_operations():
    """Verify thread-safety of DocumentationManager under concurrent page adds."""
    mgr = DocumentationManager()

    def doc_worker(idx: int):
        page = DocumentationPage(page_id=f"p_{idx}", title=f"Page_{idx}")
        mgr.add_page(page)
        return mgr.export_markdown().format == "markdown"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(doc_worker, i) for i in range(40)]
        results = [f.result() for f in futures]

    assert len(results) == 40
    assert all(results)
    assert mgr.count_pages() == 40
