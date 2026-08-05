"""API Versioning & Documentation Runtime Package (Phase 15.6).

Provider-independent Versioning & Documentation Runtime establishing models,
exceptions, ABC interfaces, version registry, compatibility manager, documentation manager,
versioning provider, runtime coordinator, and singleton accessors.
"""

from backend.application.api.versioning.compatibility_manager import (
    CompatibilityManager,
)
from backend.application.api.versioning.documentation_manager import (
    DocumentationManager,
)
from backend.application.api.versioning.exceptions import (
    CompatibilityException,
    DeprecationException,
    DocumentationException,
    VersionRegistrationException,
    VersioningException,
)
from backend.application.api.versioning.interfaces import (
    ICompatibilityManager,
    IDocumentationManager,
    IVersionRegistry,
    IVersioningProvider,
    IVersioningRuntime,
)
from backend.application.api.versioning.models import (
    ApiRelease,
    ApiVersion,
    CompatibilityReport,
    DeprecationNotice,
    DeprecationState,
    DocumentationExport,
    DocumentationPage,
    DocumentationSection,
    EndpointVersion,
    ReleaseChannel,
    VersionCapabilities,
    VersionDiagnostics,
    VersionHealth,
    VersionRuntimeState,
    VersionStatistics,
)
from backend.application.api.versioning.runtime import (
    get_versioning_provider,
    get_versioning_runtime,
    reset_versioning_provider,
    reset_versioning_runtime,
    set_versioning_provider,
    set_versioning_runtime,
)
from backend.application.api.versioning.version_registry import VersionRegistry
from backend.application.api.versioning.versioning_provider import (
    VersioningProvider,
)
from backend.application.api.versioning.versioning_runtime import (
    VersioningRuntime,
)

__all__ = [
    # Models & Enums
    "ReleaseChannel",
    "DeprecationState",
    "VersionRuntimeState",
    "DeprecationNotice",
    "EndpointVersion",
    "ApiRelease",
    "ApiVersion",
    "CompatibilityReport",
    "DocumentationSection",
    "DocumentationPage",
    "DocumentationExport",
    "VersionCapabilities",
    "VersionStatistics",
    "VersionHealth",
    "VersionDiagnostics",
    # Exceptions
    "VersioningException",
    "VersionRegistrationException",
    "CompatibilityException",
    "DocumentationException",
    "DeprecationException",
    # Interfaces
    "IVersionRegistry",
    "ICompatibilityManager",
    "IDocumentationManager",
    "IVersioningProvider",
    "IVersioningRuntime",
    # Implementations
    "VersionRegistry",
    "CompatibilityManager",
    "DocumentationManager",
    "VersioningProvider",
    "VersioningRuntime",
    # Runtime Helpers
    "get_versioning_runtime",
    "set_versioning_runtime",
    "reset_versioning_runtime",
    "get_versioning_provider",
    "set_versioning_provider",
    "reset_versioning_provider",
]
