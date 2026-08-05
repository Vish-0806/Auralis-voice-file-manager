"""API Documentation Manager Implementation (Phase 15.6).

Thread-safe documentation manager for storing, structuring, and exporting API documentation
in Markdown and JSON formats without Swagger, OpenAPI, or network dependencies.
"""

from datetime import datetime, timezone
import json
import logging
from threading import RLock
from typing import Dict, List, Optional, Tuple
import uuid

from backend.application.api.versioning.interfaces import IDocumentationManager
from backend.application.api.versioning.models import (
    DocumentationExport,
    DocumentationPage,
    DocumentationSection,
)

logger = logging.getLogger(__name__)


class DocumentationManager(IDocumentationManager):
    """Thread-safe documentation manager managing API documentation pages and export engines."""

    def __init__(self) -> None:
        """Initialize DocumentationManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._pages: Dict[str, DocumentationPage] = {}

        self._total_exports = 0

    def add_page(self, page: DocumentationPage) -> DocumentationPage:
        """Add or update a documentation page.

        Args:
            page: Immutable DocumentationPage instance.

        Returns:
            DocumentationPage: Added page instance.
        """
        with self._lock:
            self._pages[page.page_id] = page
            logger.info("Added documentation page ID '%s' (%s).", page.page_id, page.title)
            return page

    def remove_page(self, page_id: str) -> Optional[DocumentationPage]:
        """Remove a documentation page by page ID.

        Args:
            page_id: Unique page identifier.

        Returns:
            Optional[DocumentationPage]: Removed page if present, else None.
        """
        with self._lock:
            page = self._pages.pop(page_id, None)
            if page is not None:
                logger.info("Removed documentation page ID '%s'.", page_id)
            return page

    def get_page(self, page_id: str) -> Optional[DocumentationPage]:
        """Get a documentation page by page ID.

        Args:
            page_id: Unique page identifier.

        Returns:
            Optional[DocumentationPage]: Page if found, else None.
        """
        with self._lock:
            return self._pages.get(page_id)

    def list_pages(self) -> Tuple[DocumentationPage, ...]:
        """List all managed documentation pages.

        Returns:
            Tuple[DocumentationPage, ...]: Immutable tuple of pages.
        """
        with self._lock:
            return tuple(self._pages.values())

    def export_markdown(self) -> DocumentationExport:
        """Export all documentation pages as a unified Markdown document string.

        Returns:
            DocumentationExport: Resulting export object containing Markdown text.
        """
        with self._lock:
            self._total_exports += 1
            md_lines: List[str] = ["# API Documentation Archive", ""]

            for page in self._pages.values():
                md_lines.append(f"## {page.title} (v{page.version})")
                md_lines.append("")
                for sec in page.sections:
                    self._append_section_md(sec, md_lines, level=3)

            content = "\n".join(md_lines)
            export_id = f"exp_{uuid.uuid4().hex[:8]}"
            logger.info("Exported Markdown documentation (%d bytes).", len(content))
            return DocumentationExport(
                export_id=export_id,
                format="markdown",
                content=content,
                exported_at=datetime.now(timezone.utc),
            )

    def export_json(self) -> DocumentationExport:
        """Export all documentation pages as a JSON document structure string.

        Returns:
            DocumentationExport: Resulting export object containing JSON text.
        """
        with self._lock:
            self._total_exports += 1
            pages_data = [p.model_dump() for p in self._pages.values()]
            content = json.dumps({"documentation_pages": pages_data}, indent=2)
            export_id = f"exp_{uuid.uuid4().hex[:8]}"
            logger.info("Exported JSON documentation (%d bytes).", len(content))
            return DocumentationExport(
                export_id=export_id,
                format="json",
                content=content,
                exported_at=datetime.now(timezone.utc),
            )

    def count_pages(self) -> int:
        """Get total count of managed documentation pages.

        Returns:
            int: Page count.
        """
        with self._lock:
            return len(self._pages)

    def clear(self) -> None:
        """Clear all documentation pages from the manager."""
        with self._lock:
            self._pages.clear()
            logger.info("DocumentationManager cleared.")

    def _append_section_md(
        self, section: DocumentationSection, lines: List[str], level: int
    ) -> None:
        """Internal helper to recursively format section headers and text into Markdown."""
        header_prefix = "#" * level
        lines.append(f"{header_prefix} {section.title}")
        if section.content:
            lines.append(section.content)
        lines.append("")

        for sub in section.subsections:
            self._append_section_md(sub, lines, level + 1)
