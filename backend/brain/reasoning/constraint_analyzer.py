"""Constraint Analyzer Engine for deterministic extraction of structured constraints from user requests.

This module provides thread-safe constraint extraction without executing commands, calling LLMs,
creating execution plans, modifying conversations, modifying extracted goals, or accessing memory providers.
"""

from __future__ import annotations

from enum import Enum
import logging
import os
import re
import shutil
import threading
from typing import Any, Dict, List, Optional, Union

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.goal.models import Goal
from brain.reasoning.goal_extractor import GoalExtractionResult
from brain.reasoning.intent_analyzer import IntentAnalysisResult
from brain.reasoning.models import Constraint
from brain.reasoning.strategy_selector import StrategySelectionResult

logger = logging.getLogger(__name__)


class ConstraintType(str, Enum):
    """Enumeration of structured constraint types."""

    FILE_TYPE = "FILE_TYPE"
    FILE_NAME = "FILE_NAME"
    SOURCE_LOCATION = "SOURCE_LOCATION"
    DESTINATION_LOCATION = "DESTINATION_LOCATION"
    DATE_RANGE = "DATE_RANGE"
    TIME_RANGE = "TIME_RANGE"
    FILE_SIZE = "FILE_SIZE"
    FILE_EXTENSION = "FILE_EXTENSION"
    QUANTITY = "QUANTITY"
    PRIORITY = "PRIORITY"
    UNKNOWN = "UNKNOWN"


class ConstraintSeverity(str, Enum):
    """Enumeration representing severity levels for constraints."""

    OPTIONAL = "OPTIONAL"
    NORMAL = "NORMAL"
    REQUIRED = "REQUIRED"
    CRITICAL = "CRITICAL"


class ConstraintAnalysisResult(BaseModel):
    """Immutable model representing the outcome of constraint analysis."""

    model_config = ConfigDict(frozen=True)

    constraints: List[Constraint] = Field(default_factory=list)
    constraint_count: int = 0
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstraintAnalyzerConfig(BaseModel):
    """Configuration options for ConstraintAnalyzer behavior."""

    maximum_constraints: int = 100
    case_sensitive: bool = False
    strict_analysis: bool = True


DEFAULT_CONSTRAINT_PATTERNS: List[Dict[str, Any]] = [
    # FILE_TYPE
    {
        "pattern": r"\b(pdf|pdfs|photo|photos|image|images|picture|pictures|video|videos|audio|document|documents|spreadsheet|spreadsheets)\b",
        "constraint_type": ConstraintType.FILE_TYPE,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"\b(pdf|pdfs|photo|photos|image|images|picture|pictures|video|videos|audio|document|documents|spreadsheet|spreadsheets)\b",
    },
    # FILE_EXTENSION
    {
        "pattern": r"\.(pdf|png|jpg|jpeg|txt|doc|docx|csv|xlsx|zip|tar|gz|mp3|mp4|py|json|html)\b",
        "constraint_type": ConstraintType.FILE_EXTENSION,
        "severity": ConstraintSeverity.REQUIRED,
        "extraction_regex": r"\.(pdf|png|jpg|jpeg|txt|doc|docx|csv|xlsx|zip|tar|gz|mp3|mp4|py|json|html)\b",
    },
    # SOURCE_LOCATION
    {
        "pattern": r"\bfrom\s+([\"']?[\w\.\-\s\\/]+[\"']?)\b|\bin\s+(?:folder\s+)?([\"']?[\w\.\-\s\\/]+[\"']?)\b",
        "constraint_type": ConstraintType.SOURCE_LOCATION,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"(?:from|in)\s+([\"']?[\w\.\-\s\\/]+[\"']?)",
    },
    # DESTINATION_LOCATION
    {
        "pattern": r"\bto\s+([\"']?[\w\.\-\s\\/]+[\"']?)\b|\binto\s+(?:folder\s+)?([\"']?[\w\.\-\s\\/]+[\"']?)\b",
        "constraint_type": ConstraintType.DESTINATION_LOCATION,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"(?:to|into)\s+([\"']?[\w\.\-\s\\/]+[\"']?)",
    },
    # FILE_SIZE
    {
        "pattern": r"\b(larger than|greater than|smaller than|less than|>|<|over|under)\s+(\d+\s*(?:kb|mb|gb|tb|b))\b",
        "constraint_type": ConstraintType.FILE_SIZE,
        "severity": ConstraintSeverity.REQUIRED,
        "extraction_regex": r"\b(?:larger than|greater than|smaller than|less than|>|<|over|under)\s+\d+\s*(?:kb|mb|gb|tb|b)\b",
    },
    # DATE_RANGE
    {
        "pattern": r"\b(before|after|since|between|modified|created)\s+(january|february|march|april|may|june|july|august|september|october|november|december|\d{4}|yesterday|today|last week|last month)\b",
        "constraint_type": ConstraintType.DATE_RANGE,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"\b(?:before|after|since|between|modified|created)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|\d{4}|yesterday|today|last week|last month)\b",
    },
    # TIME_RANGE
    {
        "pattern": r"\b(before|after|at|between)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        "constraint_type": ConstraintType.TIME_RANGE,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"\b(?:before|after|at|between)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b",
    },
    # QUANTITY
    {
        "pattern": r"\b(top|first|last|limit)\s+(\d+)\b",
        "constraint_type": ConstraintType.QUANTITY,
        "severity": ConstraintSeverity.NORMAL,
        "extraction_regex": r"\b(?:top|first|last|limit)\s+\d+\b",
    },
    # PRIORITY
    {
        "pattern": r"\b(high priority|critical|urgent|low priority|normal priority)\b",
        "constraint_type": ConstraintType.PRIORITY,
        "severity": ConstraintSeverity.CRITICAL,
        "extraction_regex": r"\b(?:high priority|critical|urgent|low priority|normal priority)\b",
    },
    # FILE_NAME
    {
        "pattern": r"\b(?:named|name|called)\s+([\"']?[\w\.\-\s]+[\"']?)\b",
        "constraint_type": ConstraintType.FILE_NAME,
        "severity": ConstraintSeverity.REQUIRED,
        "extraction_regex": r"(?:named|name|called)\s+([\"']?[\w\.\-\s]+[\"']?)",
    },
]


class ConstraintAnalyzer:
    """Thread-safe engine for deterministic extraction of structured constraints from user requests."""

    def __init__(
        self,
        config: Optional[ConstraintAnalyzerConfig] = None,
        logger: Optional[logging.Logger] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes the ConstraintAnalyzer with optional configuration and thread lock."""
        self.config = config or ConstraintAnalyzerConfig()
        self._logger = logger or logger_instance or logging.getLogger(__name__)
        self._constraint_patterns: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

        # Pre-populate default constraint patterns
        for p in DEFAULT_CONSTRAINT_PATTERNS:
            self._constraint_patterns.append(dict(p))

    def register_constraint_pattern(
        self,
        pattern: str,
        constraint_type: ConstraintType,
        severity: ConstraintSeverity = ConstraintSeverity.NORMAL,
        extraction_regex: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a constraint pattern rule."""
        with self._lock:
            # Remove duplicate pattern entry if already registered
            self._constraint_patterns = [p for p in self._constraint_patterns if p["pattern"] != pattern]

            rule = {
                "pattern": pattern,
                "constraint_type": constraint_type,
                "severity": severity,
                "extraction_regex": extraction_regex,
                "metadata": metadata or {},
            }
            self._constraint_patterns.append(rule)
            self._logger.info("Constraint Pattern Registered: pattern=%s, constraint_type=%s", pattern, constraint_type)
            return True

    def remove_constraint_pattern(self, pattern: str) -> bool:
        """Removes a registered constraint pattern rule."""
        with self._lock:
            initial_count = len(self._constraint_patterns)
            self._constraint_patterns = [p for p in self._constraint_patterns if p["pattern"] != pattern]
            removed = len(self._constraint_patterns) < initial_count

            if removed:
                self._logger.info("Constraint Pattern Removed: pattern=%s", pattern)
                return True
            return False

    def clear_constraint_patterns(self) -> None:
        """Clears all constraint pattern rules from the registry."""
        with self._lock:
            self._constraint_patterns.clear()
            self._logger.info("Constraint Registry Cleared")

    def analyze_constraints(
        self,
        request: Any = "",
        intent_result: Optional[IntentAnalysisResult] = None,
        strategy_result: Optional[StrategySelectionResult] = None,
        goal_result: Optional[GoalExtractionResult] = None,
    ) -> Union[ConstraintAnalysisResult, List[Constraint]]:
        """Analyzes user request or Goal object for system/user constraints."""
        with self._lock:
            # Backward compatibility check for legacy Goal object input
            if isinstance(request, Goal):
                return self._analyze_legacy_goal(request)

            req_text = request if isinstance(request, str) else ""
            extracted_constraints: List[Constraint] = []

            if req_text and req_text.strip():
                flags = 0 if self.config.case_sensitive else re.IGNORECASE

                for rule in self._constraint_patterns:
                    pat = rule["pattern"]
                    try:
                        match = re.search(pat, req_text, flags=flags)
                        if match:
                            ext_regex = rule.get("extraction_regex")
                            val = match.group(0)
                            if ext_regex:
                                m_val = re.search(ext_regex, req_text, flags=flags)
                                if m_val:
                                    val = m_val.group(1) if (m_val.groups() and m_val.group(1)) else m_val.group(0)

                            const = Constraint(
                                constraint_type=rule["constraint_type"],
                                value=val.strip().strip("'\""),
                                severity=rule.get("severity", ConstraintSeverity.NORMAL),
                                reason=f"Extracted from pattern '{pat}'",
                                metadata=rule.get("metadata", {}),
                            )
                            extracted_constraints.append(const)
                            if len(extracted_constraints) >= self.config.maximum_constraints:
                                break
                    except re.error:
                        pass

            result = ConstraintAnalysisResult(
                constraints=extracted_constraints,
                constraint_count=len(extracted_constraints),
                reason="Extracted constraints successfully" if extracted_constraints else "No constraints detected",
                metadata={},
            )
            self._logger.info("Constraint Analysis Performed: constraint_count=%d", len(extracted_constraints))
            return result

    def list_constraint_patterns(
        self, constraint_type: Optional[ConstraintType] = None
    ) -> List[Dict[str, Any]]:
        """Lists registered constraint pattern rules, optionally filtered by ConstraintType."""
        with self._lock:
            if constraint_type is not None:
                return [dict(p) for p in self._constraint_patterns if p["constraint_type"] == constraint_type]
            return [dict(p) for p in self._constraint_patterns]

    def _analyze_legacy_goal(self, goal: Goal) -> List[Constraint]:
        """Legacy helper analyzing system/runtime constraints for a Goal object."""
        goal_name = goal.name.upper()
        constraints: List[Constraint] = []

        if goal_name in ["MEETING", "STUDY"]:
            satisfied = self._check_internet_connectivity()
            constraints.append(
                Constraint(
                    name="Internet Access",
                    type="internet",
                    description="Requires active internet connection to download/stream resources or join calls.",
                    satisfied=satisfied,
                )
            )

        if goal_name == "START_CODING":
            has_ide = (
                shutil.which("code") is not None
                or os.path.exists(r"C:\Program Files\Microsoft VS Code\Code.exe")
                or os.path.exists(os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Microsoft VS Code\Code.exe"))
            )
            constraints.append(
                Constraint(
                    name="VS Code Installation",
                    type="application",
                    description="Visual Studio Code must be installed on the host system.",
                    satisfied=has_ide,
                )
            )
        elif goal_name == "OPEN_APPLICATION":
            app_name = goal.parameters.get("application")
            if app_name:
                has_app = self._check_app_installed(app_name)
                constraints.append(
                    Constraint(
                        name=f"Application '{app_name}' Installed",
                        type="application",
                        description=f"Desktop application '{app_name}' must be installed and resolvable on the host system.",
                        satisfied=has_app,
                    )
                )

        if goal_name in ["LOCK_COMPUTER", "CLEAN_WORKSPACE"]:
            constraints.append(
                Constraint(
                    name="OS Session Interaction Permission",
                    type="permission",
                    description="Requires permission to lock the workstation session or manage active windows.",
                    satisfied=True,
                )
            )

        if goal_name == "ORGANIZE_DOWNLOADS":
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            has_downloads = os.path.isdir(downloads_path)
            constraints.append(
                Constraint(
                    name="Downloads Folder Existence",
                    type="file_system",
                    description="The host Downloads folder must exist and be readable.",
                    satisfied=has_downloads,
                )
            )

        self._logger.info(
            "Analyzed goal constraints",
            extra={"goal_name": goal.name, "constraints_count": len(constraints)},
        )
        return constraints

    def _check_internet_connectivity(self) -> bool:
        """Lightweight heuristic check for internet connectivity."""
        import socket
        try:
            socket.setdefaulttimeout(1.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            self._logger.debug("Internet dependency check failed: Host is offline")
            return False

    def _check_app_installed(self, app_name: str) -> bool:
        """Heuristically checks if an application exists or is in PATH."""
        if shutil.which(app_name):
            return True

        app_name_lower = app_name.lower()
        if "chrome" in app_name_lower:
            return (
                shutil.which("chrome") is not None
                or os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
                or os.path.exists(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
            )
        elif "code" in app_name_lower or "vs" in app_name_lower:
            return (
                shutil.which("code") is not None
                or os.path.exists(r"C:\Program Files\Microsoft VS Code\Code.exe")
                or os.path.exists(os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Microsoft VS Code\Code.exe"))
            )
        elif "notepad" in app_name_lower:
            return shutil.which("notepad") is not None or os.path.exists(r"C:\Windows\System32\notepad.exe")
        elif "calculator" in app_name_lower or "calc" in app_name_lower:
            return shutil.which("calc") is not None or os.path.exists(r"C:\Windows\System32\calc.exe")

        return True
