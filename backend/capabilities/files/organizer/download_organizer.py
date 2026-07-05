"""Intelligent Downloads Organizer for Auralis."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict

from .file_classifier import FileClassifier
from .organization_rules import OrganizationRules
from .report_generator import ReportGenerator


class DownloadOrganizer:
    """Manages the scanning, classification, and organization of a downloads folder."""

    def __init__(
        self,
        rules: OrganizationRules | None = None,
        classifier: FileClassifier | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the DownloadOrganizer.

        Args:
            rules: Configuration rules for category-to-folder mapping.
            classifier: Classifier implementation to categorize files.
            logger: Optional logger for diagnostics.
        """

        self._rules = rules or OrganizationRules()
        self._classifier = classifier or FileClassifier(rules=self._rules, logger=logger)
        self._logger = logger or logging.getLogger(__name__)

    def organize(self, downloads_path: str | Path) -> Dict[str, Any]:
        """Scans the downloads path, classifies every file, and moves it to the destination.

        Args:
            downloads_path: Path to the downloads folder.

        Returns:
            A dictionary containing status, summary report string, and raw details data.
        """

        report = ReportGenerator()
        path = Path(downloads_path).expanduser().resolve()

        if not path.exists() or not path.is_dir():
            error_msg = f"Downloads path '{downloads_path}' does not exist or is not a directory."
            self._logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "report": "",
                "data": {},
            }

        try:
            entries = list(path.iterdir())
        except PermissionError as exc:
            self._logger.exception("Permission error scanning downloads directory")
            return {
                "status": "error",
                "message": f"Permission denied scanning '{downloads_path}'.",
                "report": "",
                "data": {},
            }
        except Exception as exc:
            self._logger.exception("Unexpected error scanning downloads directory")
            return {
                "status": "error",
                "message": f"Failed to scan '{downloads_path}': {exc}",
                "report": "",
                "data": {},
            }

        for entry in entries:
            # Skip directories
            if entry.is_dir():
                continue

            report.log_scanned(str(entry))

            # Safety: ignore hidden and system files
            if self._is_hidden_or_system(entry):
                report.log_skipped(str(entry), "Hidden or system file")
                continue

            try:
                category = self._classifier.classify(entry)
                folder_name = self._rules.get_folder_for_category(category)
                category_dir = path / folder_name

                # Reuse folders if already present, or create them
                if not category_dir.exists():
                    category_dir.mkdir(parents=True, exist_ok=True)
                elif not category_dir.is_dir():
                    report.log_skipped(
                        str(entry),
                        f"Cannot organize into '{folder_name}' because a non-directory file with that name exists"
                    )
                    continue

                dest_path = self._get_unique_path(category_dir, entry.name)

                self._logger.info(
                    "Moving file",
                    extra={"source": str(entry), "destination": str(dest_path), "category": category}
                )

                # Move the file safely using shutil.move
                shutil.move(str(entry), str(dest_path))
                report.log_moved(str(entry), str(dest_path), category)

            except PermissionError as exc:
                self._logger.warning("Permission error organizing file", extra={"file": str(entry), "error": str(exc)})
                report.log_error(str(entry), f"PermissionError: {exc}")
            except Exception as exc:
                self._logger.exception("Error organizing file", extra={"file": str(entry)})
                report.log_error(str(entry), f"{exc.__class__.__name__}: {exc}")

        summary_text = report.generate_summary()
        self._logger.info("Downloads organization complete")

        return {
            "status": "success",
            "message": "Downloads folder organized successfully.",
            "report": summary_text,
            "data": report.get_data(),
        }

    def _is_hidden_or_system(self, path: Path) -> bool:
        """Checks if a file is hidden or system-related.

        Args:
            path: Path to evaluate.

        Returns:
            True if the file should be ignored, otherwise False.
        """

        if path.name.startswith("."):
            return True

        # Windows hidden/system attributes
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:
                # FILE_ATTRIBUTE_HIDDEN = 2
                # FILE_ATTRIBUTE_SYSTEM = 4
                if attrs & (2 | 4):
                    return True
        except Exception:
            pass

        # Common Windows-specific hidden/system files
        if path.name.lower() in {"desktop.ini", "thumbs.db", "ntuser.dat", "ntuser.ini"}:
            return True

        return False

    def _get_unique_path(self, target_folder: Path, filename: str) -> Path:
        """Resolves duplicate filenames by appending a counter.

        Args:
            target_folder: Directory to place the file in.
            filename: Original name of the file.

        Returns:
            A unique Path that does not currently exist.
        """

        name = Path(filename).stem
        suffix = Path(filename).suffix
        dest_path = target_folder / filename
        counter = 1
        while dest_path.exists():
            dest_path = target_folder / f"{name}_{counter}{suffix}"
            counter += 1
        return dest_path
