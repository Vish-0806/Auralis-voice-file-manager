"""File classification logic for sorting files based on organization rules.

Designed for future AI/ML integration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from .organization_rules import OrganizationRules


class FileClassifier:
    """Classifies files into categories based on organization rules.

    This is structured as a rule-based classifier that can be subclassed or
    extended in the future for AI-based semantic/content classification.
    """

    def __init__(
        self,
        rules: OrganizationRules | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the classifier.

        Args:
            rules: Configuration rules for the classification.
            logger: Optional logger for diagnostics.
        """

        self._rules = rules or OrganizationRules()
        self._logger = logger or logging.getLogger(__name__)

    def classify(self, file_path: Path) -> str:
        """Determines the category for a given file.

        This method is designed to allow future AI enhancements (e.g. content inspection,
        NLP on filename/contents) without changing the callers.

        Args:
            file_path: The Path object of the file to classify.

        Returns:
            The category name (e.g., 'PDF', 'Images', 'Others').
        """

        extension = file_path.suffix
        category = self._rules.get_category_for_extension(extension)

        self._logger.debug(
            "Classified file",
            extra={"path": str(file_path), "extension": extension, "category": category}
        )
        return category
