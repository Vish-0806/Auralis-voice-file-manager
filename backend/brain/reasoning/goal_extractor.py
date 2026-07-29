"""Goal Extraction Engine for extracting structured goals from user requests.

This module provides thread-safe goal extraction without executing commands, calling LLMs,
creating execution plans, modifying conversations, or accessing memory providers.
"""

from enum import Enum
import logging
import re
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

from brain.reasoning.intent_analyzer import IntentAnalysisResult, IntentCategory
from brain.reasoning.strategy_selector import ReasoningStrategy, StrategySelectionResult

logger = logging.getLogger(__name__)


class GoalType(str, Enum):
    """Enumeration of structured goal types."""

    MOVE_FILES = "MOVE_FILES"
    COPY_FILES = "COPY_FILES"
    DELETE_FILES = "DELETE_FILES"
    RENAME_FILES = "RENAME_FILES"
    SEARCH_FILES = "SEARCH_FILES"
    OPEN_FILE = "OPEN_FILE"
    CREATE_FOLDER = "CREATE_FOLDER"
    DELETE_FOLDER = "DELETE_FOLDER"
    SCHEDULE_TASK = "SCHEDULE_TASK"
    ANSWER_QUESTION = "ANSWER_QUESTION"
    GENERAL_TASK = "GENERAL_TASK"
    UNKNOWN = "UNKNOWN"


class GoalPriority(str, Enum):
    """Enumeration representing priority levels for extracted goals."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GoalExtractionResult(BaseModel):
    """Immutable model representing the outcome of goal extraction."""

    model_config = ConfigDict(frozen=True)

    goal_type: GoalType = GoalType.UNKNOWN
    priority: GoalPriority = GoalPriority.NORMAL
    action: str = ""
    objects: List[str] = Field(default_factory=list)
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoalExtractorConfig(BaseModel):
    """Configuration options for GoalExtractor behavior."""

    maximum_objects: int = 100
    case_sensitive: bool = False
    strict_extraction: bool = True


DEFAULT_GOAL_PATTERNS: List[Dict[str, Any]] = [
    # MOVE_FILES
    {
        "pattern": r"\b(move|transfer)\b",
        "goal_type": GoalType.MOVE_FILES,
        "action": "move",
        "priority": GoalPriority.HIGH,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip)\b|\b[\w\.\-\*]+(?:\s+files?|\s+documents?))",
    },
    # COPY_FILES
    {
        "pattern": r"\b(copy|duplicate)\b",
        "goal_type": GoalType.COPY_FILES,
        "action": "copy",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip)\b|\b[\w\.\-\*]+(?:\s+files?|\s+photos?|\s+documents?))",
    },
    # DELETE_FILES
    {
        "pattern": r"\b(delete|remove|trash)\s+(?:file|files|temp|document|pdf|png|jpg|txt)\b|\b(delete|remove)\s+[\w\.\-\*]+\.[\w]+\b|\bdelete temp files\b",
        "goal_type": GoalType.DELETE_FILES,
        "action": "delete",
        "priority": GoalPriority.HIGH,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip|temp|tmp)\b|\btemp files?\b|\b[\w\.\-\*]+\b)",
    },
    # RENAME_FILES
    {
        "pattern": r"\b(rename)\b",
        "goal_type": GoalType.RENAME_FILES,
        "action": "rename",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip)\b|\b[\w\.\-\*]+\b)",
    },
    # SEARCH_FILES
    {
        "pattern": r"\b(find|search|locate|list files)\b",
        "goal_type": GoalType.SEARCH_FILES,
        "action": "search",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip)\b|\binvoices?\b|\bpdfs?\b|\bdocuments?\b|\b[\w\.\-\*]+\b)",
    },
    # OPEN_FILE
    {
        "pattern": r"\b(open|view|show)\b",
        "goal_type": GoalType.OPEN_FILE,
        "action": "open",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\b[\w\.\-\*]+\.(?:pdf|png|jpg|txt|doc|docx|csv|xlsx|zip)\b|\b[\w\.\-\*]+\b)",
    },
    # CREATE_FOLDER
    {
        "pattern": r"\b(create|make)\s+(?:folder|directory|project folder)\b|\bmkdir\b",
        "goal_type": GoalType.CREATE_FOLDER,
        "action": "create_folder",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(?:folder|directory|mkdir)\s+([\"']?[\w\.\-\s]+[\"']?)",
    },
    # DELETE_FOLDER
    {
        "pattern": r"\b(delete|remove)\s+(?:folder|directory|old folder)\b|\brmdir\b",
        "goal_type": GoalType.DELETE_FOLDER,
        "action": "delete_folder",
        "priority": GoalPriority.HIGH,
        "object_pattern": r"(?:folder|directory|rmdir)\s+([\"']?[\w\.\-\s]+[\"']?)",
    },
    # SCHEDULE_TASK
    {
        "pattern": r"\b(schedule|cron|repeat|run every|timer|alarm)\b",
        "goal_type": GoalType.SCHEDULE_TASK,
        "action": "schedule",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\bbackup\b|\btask\b|\bjob\b|\b[\w\.\-\*]+\b)",
    },
    # ANSWER_QUESTION
    {
        "pattern": r"\b(what is|how to|explain|describe|tell me|why does|who is)\b",
        "goal_type": GoalType.ANSWER_QUESTION,
        "action": "answer_question",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(?:what is|how to|explain|describe|tell me about|why does)\s+([\"']?[\w\.\-\s\?]+[\"']?)",
    },
    # GENERAL_TASK
    {
        "pattern": r"\b(do|process|execute|run)\s+(?:task|something|pipeline)\b",
        "goal_type": GoalType.GENERAL_TASK,
        "action": "general_task",
        "priority": GoalPriority.NORMAL,
        "object_pattern": r"(\btask\b|\bpipeline\b|\b[\w\.\-\*]+\b)",
    },
]

PRIORITY_RANK = {
    GoalPriority.CRITICAL: 4,
    GoalPriority.HIGH: 3,
    GoalPriority.NORMAL: 2,
    GoalPriority.LOW: 1,
}


class GoalExtractor:
    """Thread-safe engine for extracting structured goals from user requests."""

    def __init__(self, config: Optional[GoalExtractorConfig] = None) -> None:
        """Initializes the GoalExtractor with optional configuration and thread lock."""
        self.config = config or GoalExtractorConfig()
        self._goal_patterns: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

        # Pre-populate default goal pattern rules
        for p in DEFAULT_GOAL_PATTERNS:
            self._goal_patterns.append(dict(p))

    def register_goal_pattern(
        self,
        pattern: str,
        goal_type: GoalType,
        action: str = "",
        priority: GoalPriority = GoalPriority.NORMAL,
        object_pattern: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a goal pattern rule."""
        with self._lock:
            # Remove existing duplicate pattern if present
            self._goal_patterns = [p for p in self._goal_patterns if p["pattern"] != pattern]

            rule = {
                "pattern": pattern,
                "goal_type": goal_type,
                "action": action,
                "priority": priority,
                "object_pattern": object_pattern,
                "metadata": metadata or {},
            }
            self._goal_patterns.append(rule)
            logger.info("Goal Pattern Registered: pattern=%s, goal_type=%s", pattern, goal_type)
            return True

    def remove_goal_pattern(self, pattern: str) -> bool:
        """Removes a registered goal pattern rule."""
        with self._lock:
            initial_count = len(self._goal_patterns)
            self._goal_patterns = [p for p in self._goal_patterns if p["pattern"] != pattern]
            removed = len(self._goal_patterns) < initial_count

            if removed:
                logger.info("Goal Pattern Removed: pattern=%s", pattern)
                return True
            return False

    def clear_goal_patterns(self) -> None:
        """Clears all goal pattern rules from the registry."""
        with self._lock:
            self._goal_patterns.clear()
            logger.info("Goal Registry Cleared")

    def extract_goals(
        self,
        request: str,
        intent_result: Optional[IntentAnalysisResult] = None,
        strategy_result: Optional[StrategySelectionResult] = None,
    ) -> GoalExtractionResult:
        """Deterministically extracts structured goals from user request text and optional intent/strategy results."""
        with self._lock:
            if not isinstance(request, str) or not request.strip():
                result = GoalExtractionResult(
                    goal_type=GoalType.UNKNOWN,
                    priority=GoalPriority.LOW,
                    action="",
                    objects=[],
                    reason="Empty or invalid request input",
                    metadata={},
                )
                logger.info("Goal Extraction Performed: goal_type=%s", result.goal_type)
                return result

            matches: List[Dict[str, Any]] = []
            flags = 0 if self.config.case_sensitive else re.IGNORECASE

            for rule in self._goal_patterns:
                pat = rule["pattern"]
                try:
                    if re.search(pat, request, flags=flags):
                        matches.append(rule)
                except re.error:
                    pass

            if not matches:
                # Guided fallback via intent or strategy if present
                fallback_goal = GoalType.UNKNOWN
                if intent_result:
                    if intent_result.intent == IntentCategory.FILE_SEARCH:
                        fallback_goal = GoalType.SEARCH_FILES
                    elif intent_result.intent == IntentCategory.QUESTION_ANSWERING:
                        fallback_goal = GoalType.ANSWER_QUESTION
                    elif intent_result.intent == IntentCategory.SCHEDULING:
                        fallback_goal = GoalType.SCHEDULE_TASK

                result = GoalExtractionResult(
                    goal_type=fallback_goal,
                    priority=GoalPriority.LOW,
                    action="",
                    objects=[],
                    reason="No pattern matched, guided fallback applied" if fallback_goal != GoalType.UNKNOWN else "No matching goal pattern found",
                    metadata={},
                )
                logger.info("Goal Extraction Performed: goal_type=%s", result.goal_type)
                return result

            # Sort matches by priority descending
            matches.sort(
                key=lambda m: PRIORITY_RANK.get(m.get("priority", GoalPriority.NORMAL), 2),
                reverse=True,
            )

            best_match = matches[0]
            extracted_objects = self._extract_objects(request, best_match)

            result = GoalExtractionResult(
                goal_type=best_match["goal_type"],
                priority=best_match.get("priority", GoalPriority.NORMAL),
                action=best_match.get("action", ""),
                objects=extracted_objects,
                reason=f"Extracted goal '{best_match['goal_type']}' from pattern match",
                metadata=best_match.get("metadata", {}),
            )
            logger.info("Goal Extraction Performed: goal_type=%s", result.goal_type)
            return result

    def _extract_objects(self, request: str, rule: Dict[str, Any]) -> List[str]:
        """Helper to extract target object entities from request string."""
        raw_objects: List[str] = []
        obj_pat = rule.get("object_pattern")
        flags = 0 if self.config.case_sensitive else re.IGNORECASE

        if obj_pat:
            try:
                for match in re.finditer(obj_pat, request, flags=flags):
                    val = match.group(1) if match.groups() else match.group(0)
                    if val and val.strip():
                        raw_objects.append(val.strip().strip("'\""))
            except re.error:
                pass

        # Fallback regex for filenames with extensions or quoted names
        if not raw_objects:
            file_matches = re.findall(r"\b[\w\.\-\*]+\.[\w]+\b", request)
            raw_objects.extend(file_matches)

        # Deduplicate preserving order and enforce limit
        seen = set()
        final_objects = []
        for obj in raw_objects:
            obj_clean = obj if self.config.case_sensitive else obj.lower()
            if obj_clean not in seen:
                seen.add(obj_clean)
                final_objects.append(obj)
                if len(final_objects) >= self.config.maximum_objects:
                    break

        return final_objects

    def list_goal_patterns(self, goal_type: Optional[GoalType] = None) -> List[Dict[str, Any]]:
        """Lists registered goal pattern rules, optionally filtered by GoalType."""
        with self._lock:
            if goal_type is not None:
                return [dict(p) for p in self._goal_patterns if p["goal_type"] == goal_type]
            return [dict(p) for p in self._goal_patterns]
