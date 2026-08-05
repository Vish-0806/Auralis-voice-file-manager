"""API Versioning & Documentation Interfaces (Phase 15.6).

Defines Abstract Base Classes (ABCs) establishing design contracts for the Version
Registry, Compatibility Manager, Documentation Manager, Versioning Provider, and Versioning Runtime.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from backend.application.api.versioning.models import (
    ApiVersion,
    CompatibilityReport,
    DocumentationExport,
    DocumentationPage,
    ReleaseChannel,
    VersionCapabilities,
    VersionDiagnostics,
    VersionHealth,
    VersionStatistics,
)


class IVersionRegistry(ABC):
    """Abstract interface for the API Version Registry."""

    @abstractmethod
    def register_version(self, version: ApiVersion) -> ApiVersion:
        """Register a new API version definition.

        Args:
            version: Immutable ApiVersion instance.

        Returns:
            ApiVersion: Registered version.

        Raises:
            VersionRegistrationException: If registration fails or version_id/number exists.
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_version(self, version_id: str) -> Optional[ApiVersion]:
        """Unregister an API version by version ID.

        Args:
            version_id: Unique version identifier.

        Returns:
            Optional[ApiVersion]: Removed version if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def lookup_version(self, version_id: str) -> Optional[ApiVersion]:
        """Look up an API version by ID.

        Args:
            version_id: Unique version identifier.

        Returns:
            Optional[ApiVersion]: ApiVersion model if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_version(
        self, channel: Optional[ReleaseChannel] = None
    ) -> Optional[ApiVersion]:
        """Get the latest registered version, optionally filtered by release channel.

        Args:
            channel: Optional ReleaseChannel filter.

        Returns:
            Optional[ApiVersion]: Latest version if registered, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_versions(
        self, channel: Optional[ReleaseChannel] = None
    ) -> Tuple[ApiVersion, ...]:
        """List registered versions, optionally filtered by release channel.

        Args:
            channel: Optional ReleaseChannel filter.

        Returns:
            Tuple[ApiVersion, ...]: Tuple of matching versions.
        """
        raise NotImplementedError

    @abstractmethod
    def count_versions(self) -> int:
        """Get total count of registered API versions.

        Returns:
            int: Version count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all registered versions from the registry."""
        raise NotImplementedError


class ICompatibilityManager(ABC):
    """Abstract interface for the Compatibility Manager."""

    @abstractmethod
    def evaluate_compatibility(
        self, base_version: ApiVersion, target_version: ApiVersion
    ) -> CompatibilityReport:
        """Evaluate compatibility between two ApiVersion model instances.

        Args:
            base_version: Base/older version.
            target_version: Target/newer version.

        Returns:
            CompatibilityReport: Resulting compatibility evaluation report.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_version_strings(
        self, base_ver: str, target_ver: str
    ) -> CompatibilityReport:
        """Evaluate compatibility between two version string representations (e.g. '1.0.0' vs '2.0.0').

        Args:
            base_ver: Base version string.
            target_ver: Target version string.

        Returns:
            CompatibilityReport: Resulting compatibility evaluation report.
        """
        raise NotImplementedError


class IDocumentationManager(ABC):
    """Abstract interface for the Documentation Manager."""

    @abstractmethod
    def add_page(self, page: DocumentationPage) -> DocumentationPage:
        """Add a new documentation page.

        Args:
            page: Immutable DocumentationPage instance.

        Returns:
            DocumentationPage: Added page.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_page(self, page_id: str) -> Optional[DocumentationPage]:
        """Remove a documentation page by page ID.

        Args:
            page_id: Unique page identifier.

        Returns:
            Optional[DocumentationPage]: Removed page if present, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def get_page(self, page_id: str) -> Optional[DocumentationPage]:
        """Get a documentation page by page ID.

        Args:
            page_id: Unique page identifier.

        Returns:
            Optional[DocumentationPage]: Page if found, else None.
        """
        raise NotImplementedError

    @abstractmethod
    def list_pages(self) -> Tuple[DocumentationPage, ...]:
        """List all managed documentation pages.

        Returns:
            Tuple[DocumentationPage, ...]: Tuple of documentation pages.
        """
        raise NotImplementedError

    @abstractmethod
    def export_markdown(self) -> DocumentationExport:
        """Export all documentation pages as a unified Markdown document.

        Returns:
            DocumentationExport: Export result object containing Markdown text.
        """
        raise NotImplementedError

    @abstractmethod
    def export_json(self) -> DocumentationExport:
        """Export all documentation pages as a JSON document structure.

        Returns:
            DocumentationExport: Export result object containing JSON text.
        """
        raise NotImplementedError

    @abstractmethod
    def count_pages(self) -> int:
        """Get total count of managed documentation pages.

        Returns:
            int: Page count.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Clear all documentation pages from the manager."""
        raise NotImplementedError


class IVersioningProvider(ABC):
    """Abstract interface for the Versioning Provider."""

    @abstractmethod
    def initialize(self) -> VersionHealth:
        """Initialize the versioning provider.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> VersionHealth:
        """Shutdown the versioning provider safely.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> VersionHealth:
        """Restart the versioning provider.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> VersionHealth:
        """Get health evaluation snapshot.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> VersionStatistics:
        """Get aggregate statistics.

        Returns:
            VersionStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> VersionCapabilities:
        """Get declared capabilities.

        Returns:
            VersionCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> VersionDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            VersionDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_version_registry(self) -> IVersionRegistry:
        """Get encapsulated version registry.

        Returns:
            IVersionRegistry: Version registry.
        """
        raise NotImplementedError

    @abstractmethod
    def get_compatibility_manager(self) -> ICompatibilityManager:
        """Get encapsulated compatibility manager.

        Returns:
            ICompatibilityManager: Compatibility manager.
        """
        raise NotImplementedError

    @abstractmethod
    def get_documentation_manager(self) -> IDocumentationManager:
        """Get encapsulated documentation manager.

        Returns:
            IDocumentationManager: Documentation manager.
        """
        raise NotImplementedError


class IVersioningRuntime(ABC):
    """Abstract interface for the Versioning Runtime."""

    @abstractmethod
    def initialize(self) -> VersionHealth:
        """Initialize the versioning runtime.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> VersionHealth:
        """Shutdown the versioning runtime safely.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> VersionHealth:
        """Restart the versioning runtime.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> VersionHealth:
        """Get health evaluation snapshot.

        Returns:
            VersionHealth: Health snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self) -> VersionStatistics:
        """Get aggregate statistics.

        Returns:
            VersionStatistics: Statistics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> VersionCapabilities:
        """Get declared capabilities.

        Returns:
            VersionCapabilities: Capabilities snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> VersionDiagnostics:
        """Get diagnostic telemetry.

        Returns:
            VersionDiagnostics: Diagnostics snapshot.
        """
        raise NotImplementedError

    @abstractmethod
    def get_provider(self) -> IVersioningProvider:
        """Get encapsulated versioning provider.

        Returns:
            IVersioningProvider: Versioning provider.
        """
        raise NotImplementedError
