"""Configurable organization rules for sorting downloads in Auralis."""

from __future__ import annotations

from typing import Dict, Set


class OrganizationRules:
    """Defines and manages configurable organization rules for file classification.

    This class maps extensions to standard categories, and maps categories to
    destination folder names.
    """

    DEFAULT_CATEGORY_FOLDERS: Dict[str, str] = {
        "Documents": "Documents",
        "Images": "Images",
        "Videos": "Videos",
        "Audio": "Audio",
        "Archives": "Archives",
        "Executables": "Executables",
        "Code": "Code",
        "Spreadsheets": "Spreadsheets",
        "Presentations": "Presentations",
        "PDF": "PDF",
        "Text": "Text",
        "Others": "Others",
    }

    DEFAULT_EXTENSION_MAP: Dict[str, Set[str]] = {
        "PDF": {".pdf"},
        "Text": {".txt", ".rtf", ".odt"},
        "Spreadsheets": {".xlsx", ".xls", ".csv", ".numbers", ".ods"},
        "Presentations": {".pptx", ".ppt", ".key", ".odp"},
        "Documents": {".docx", ".doc", ".pages", ".epub"},
        "Images": {
            ".png", ".jpg", ".jpeg", ".gif", ".webp",
            ".bmp", ".tiff", ".svg", ".heic", ".heif", ".ico"
        },
        "Videos": {
            ".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv",
            ".m4v", ".webm", ".3gp"
        },
        "Audio": {
            ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma"
        },
        "Archives": {
            ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz",
            ".bz2", ".xz"
        },
        "Executables": {
            ".exe", ".msi", ".dmg", ".pkg", ".app", ".deb", ".rpm"
        },
        "Code": {
            ".py", ".java", ".js", ".cpp", ".c", ".html", ".css",
            ".ts", ".sh", ".bat", ".json", ".xml", ".yaml", ".yml",
            ".md", ".go", ".rs", ".cs", ".sql", ".h", ".php"
        },
    }

    def __init__(
        self,
        category_folders: Dict[str, str] | None = None,
        extension_map: Dict[str, Set[str]] | None = None,
    ) -> None:
        """Initializes the organization rules.

        Args:
            category_folders: Custom mapping of category name to folder name.
            extension_map: Custom mapping of category name to a set of extensions.
        """

        self.category_folders = category_folders or self.DEFAULT_CATEGORY_FOLDERS.copy()
        self.extension_map = extension_map or self.DEFAULT_EXTENSION_MAP.copy()

    def get_folder_for_category(self, category: str) -> str:
        """Returns the folder name mapped to a given category.

        Args:
            category: The file category.

        Returns:
            The folder name mapped to the category, defaulting to the category name itself.
        """

        return self.category_folders.get(category, category)

    def get_category_for_extension(self, extension: str) -> str:
        """Determines the category for a given extension.

        Args:
            extension: The file extension (e.g. '.pdf').

        Returns:
            The matching category name, or 'Others' if unmatched.
        """

        normalized_ext = extension.strip().lower()
        for category, extensions in self.extension_map.items():
            if normalized_ext in extensions:
                return category
        return "Others"
