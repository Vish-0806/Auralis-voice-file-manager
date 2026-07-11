"""Failure analyzer classifying runtime exceptions into standard failure types for Auralis."""

from __future__ import annotations

import logging
from .models import FailureType


class FailureAnalyzer:
    """Classifies raw execution error messages into canonical FailureType enums."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the FailureAnalyzer.

        Args:
            logger: Optional custom logger for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def analyze_failure(self, error_message: str) -> FailureType:
        """Analyzes an error message and classifies it.

        Args:
            error_message: Raw error response or exception trace.

        Returns:
            The resolved FailureType.
        """
        if not error_message:
            return FailureType.UNKNOWN

        error_lower = error_message.lower()

        if any(term in error_lower for term in ["executable path", "application not found", "could not resolve executable", "app not found", "program not found"]):
            return FailureType.APPLICATION_NOT_FOUND

        if any(term in error_lower for term in ["file not found", "directory not found", "filenotfounderror", "path not found", "no such file"]):
            return FailureType.FILE_NOT_FOUND

        if any(term in error_lower for term in ["permission denied", "permissionerror", "access denied", "unauthorized", "privilege required"]):
            return FailureType.PERMISSION_DENIED

        if any(term in error_lower for term in ["network unavailable", "host is offline", "socket.error", "connection refused", "dns resolution", "offline", "networkerror"]):
            return FailureType.NETWORK_UNAVAILABLE

        if any(term in error_lower for term in ["timeout", "timed out", "timeouterror", "expired"]):
            return FailureType.TIMEOUT

        self._logger.debug("Error message did not match any custom failure types", extra={"error": error_message})
        return FailureType.UNKNOWN
