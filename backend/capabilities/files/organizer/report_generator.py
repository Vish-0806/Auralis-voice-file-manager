"""Report generator for compiling organization run summaries."""

from __future__ import annotations

from typing import Dict, List


class ReportGenerator:
    """Compiles a detailed text summary and structured data of the organization run."""

    def __init__(self) -> None:
        """Initializes the report generator."""

        self._scanned: List[str] = []
        self._moved: Dict[str, str] = {}  # src -> dest
        self._skipped: List[tuple[str, str]] = []  # path, reason
        self._errors: List[tuple[str, str]] = []  # path, error message
        self._categories: Dict[str, int] = {}  # category -> count

    def log_scanned(self, file_path: str) -> None:
        """Logs a scanned file."""

        self._scanned.append(file_path)

    def log_moved(self, src: str, dest: str, category: str) -> None:
        """Logs a successfully moved file."""

        self._moved[src] = dest
        self._categories[category] = self._categories.get(category, 0) + 1

    def log_skipped(self, file_path: str, reason: str) -> None:
        """Logs a skipped file."""

        self._skipped.append((file_path, reason))

    def log_error(self, file_path: str, error: str) -> None:
        """Logs an error encountered during file processing."""

        self._errors.append((file_path, error))

    def generate_summary(self) -> str:
        """Generates a structured human-readable text summary of the run."""

        summary_lines = [
            "Downloads Organization Report",
            "============================",
            f"Files Scanned: {len(self._scanned)}",
            f"Files Organized: {len(self._moved)}",
            f"Files Skipped: {len(self._skipped)}",
            f"Errors: {len(self._errors)}",
            "",
            "Categories Summary:",
        ]
        if self._categories:
            for cat, count in sorted(self._categories.items()):
                summary_lines.append(f"  - {cat}: {count} file(s)")
        else:
            summary_lines.append("  No files categorized.")

        if self._skipped:
            summary_lines.extend(["", "Skipped Files Details:"])
            for path, reason in self._skipped[:10]:
                summary_lines.append(f"  - {path}: {reason}")
            if len(self._skipped) > 10:
                summary_lines.append(f"  ... and {len(self._skipped) - 10} more")

        if self._errors:
            summary_lines.extend(["", "Errors Details:"])
            for path, err in self._errors[:10]:
                summary_lines.append(f"  - {path}: {err}")
            if len(self._errors) > 10:
                summary_lines.append(f"  ... and {len(self._errors) - 10} more")

        return "\n".join(summary_lines)

    def get_data(self) -> dict:
        """Returns the raw structured data representing the run details."""

        return {
            "scanned": self._scanned,
            "moved": self._moved,
            "skipped": [{"path": p, "reason": r} for p, r in self._skipped],
            "errors": [{"path": p, "error": e} for p, e in self._errors],
            "categories": self._categories,
            "scanned_count": len(self._scanned),
            "moved_count": len(self._moved),
            "skipped_count": len(self._skipped),
            "error_count": len(self._errors),
        }
