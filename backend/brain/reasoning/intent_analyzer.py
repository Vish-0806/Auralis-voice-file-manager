"""Intent Analysis Engine for deterministic classification of user requests into intent categories.

This module provides thread-safe intent classification without executing commands,
calling LLMs, creating execution plans, modifying conversations, or accessing memory providers.
"""

from enum import Enum
import logging
import re
import threading
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    """Enumeration of structured intent categories."""

    FILE_MANAGEMENT = "FILE_MANAGEMENT"
    FILE_SEARCH = "FILE_SEARCH"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    CONVERSATION = "CONVERSATION"
    PLANNING = "PLANNING"
    SCHEDULING = "SCHEDULING"
    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"


class IntentConfidence(str, Enum):
    """Enumeration representing confidence levels for intent classification."""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class IntentAnalysisResult(BaseModel):
    """Immutable model representing the outcome of intent classification."""

    model_config = ConfigDict(frozen=True)

    intent: IntentCategory = IntentCategory.UNKNOWN
    confidence: IntentConfidence = IntentConfidence.VERY_LOW
    matched_patterns: List[str] = Field(default_factory=list)
    reason: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentAnalyzerConfig(BaseModel):
    """Configuration options for IntentAnalyzer limits and matching behavior."""

    minimum_confidence: float = 0.50
    maximum_patterns: int = 500
    case_sensitive: bool = False


DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    # FILE_MANAGEMENT
    {"pattern": r"\b(move|moving|transfer)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(rename|renaming)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(delete|remove|trash)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(copy|duplicate)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(create directory|make folder|create folder|mkdir)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(organize|sorting|cleanup|compress|zip|unzip)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.HIGH, "priority": 9, "is_regex": True},
    {"pattern": r"\b(file|folder|directory)\b", "intent": IntentCategory.FILE_MANAGEMENT, "confidence": IntentConfidence.MEDIUM, "priority": 5, "is_regex": True},

    # FILE_SEARCH
    {"pattern": r"\b(search|find|locate|where is|list files)\b", "intent": IntentCategory.FILE_SEARCH, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(find pdfs|locate document|find images|search for)\b", "intent": IntentCategory.FILE_SEARCH, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(filter by|extension|modified date)\b", "intent": IntentCategory.FILE_SEARCH, "confidence": IntentConfidence.MEDIUM, "priority": 6, "is_regex": True},

    # QUESTION_ANSWERING
    {"pattern": r"\b(what is|how to|explain|describe|tell me about|why does)\b", "intent": IntentCategory.QUESTION_ANSWERING, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(who is|where can i|how can i)\b", "intent": IntentCategory.QUESTION_ANSWERING, "confidence": IntentConfidence.MEDIUM, "priority": 8, "is_regex": True},

    # CONVERSATION
    {"pattern": r"\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b", "intent": IntentCategory.CONVERSATION, "confidence": IntentConfidence.VERY_HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(thanks|thank you|bye|goodbye|see ya|how are you)\b", "intent": IntentCategory.CONVERSATION, "confidence": IntentConfidence.VERY_HIGH, "priority": 10, "is_regex": True},

    # PLANNING
    {"pattern": r"\b(plan|create workflow|build pipeline|multi-step|strategy|map out)\b", "intent": IntentCategory.PLANNING, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(workflow|step by step|execution sequence)\b", "intent": IntentCategory.PLANNING, "confidence": IntentConfidence.MEDIUM, "priority": 8, "is_regex": True},

    # SCHEDULING
    {"pattern": r"\b(schedule|cron|run every|repeat|timer|alarm|daily|weekly)\b", "intent": IntentCategory.SCHEDULING, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(reminder|recurring|at 5pm|every hour)\b", "intent": IntentCategory.SCHEDULING, "confidence": IntentConfidence.MEDIUM, "priority": 8, "is_regex": True},

    # SYSTEM_CONTROL
    {"pattern": r"\b(volume|mute|unmute|brightness|screenshot|screen capture)\b", "intent": IntentCategory.SYSTEM_CONTROL, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(shutdown system|reboot|restart|lock screen|sleep mode)\b", "intent": IntentCategory.SYSTEM_CONTROL, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},

    # HELP
    {"pattern": r"\b(help|manual|usage|how do i use|documentation|commands)\b", "intent": IntentCategory.HELP, "confidence": IntentConfidence.HIGH, "priority": 10, "is_regex": True},
    {"pattern": r"\b(guide|instructions|what can you do)\b", "intent": IntentCategory.HELP, "confidence": IntentConfidence.MEDIUM, "priority": 8, "is_regex": True},
]


CONFIDENCE_RANK = {
    IntentConfidence.VERY_HIGH: 5,
    IntentConfidence.HIGH: 4,
    IntentConfidence.MEDIUM: 3,
    IntentConfidence.LOW: 2,
    IntentConfidence.VERY_LOW: 1,
}


class IntentAnalyzer:
    """Thread-safe engine for deterministic classification of user requests into intent categories."""

    def __init__(self, config: Optional[IntentAnalyzerConfig] = None) -> None:
        """Initializes the IntentAnalyzer with optional configuration and thread lock."""
        self.config = config or IntentAnalyzerConfig()
        self._pattern_registry: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

        # Pre-populate default pattern rules
        for p in DEFAULT_PATTERNS:
            self._pattern_registry.append(dict(p))

    def register_pattern(
        self,
        pattern: str,
        intent: IntentCategory,
        confidence: IntentConfidence = IntentConfidence.HIGH,
        priority: int = 1,
        is_regex: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Registers a new pattern rule for intent classification."""
        with self._lock:
            if len(self._pattern_registry) >= self.config.maximum_patterns:
                return False

            # Remove duplicate pattern entry if already registered
            self._pattern_registry = [p for p in self._pattern_registry if p["pattern"] != pattern]

            rule = {
                "pattern": pattern,
                "intent": intent,
                "confidence": confidence,
                "priority": priority,
                "is_regex": is_regex,
                "metadata": metadata or {},
            }
            self._pattern_registry.append(rule)
            logger.info("Pattern Registered: pattern=%s, intent=%s", pattern, intent)
            return True

    def remove_pattern(self, pattern: str) -> bool:
        """Removes a registered pattern rule."""
        with self._lock:
            initial_count = len(self._pattern_registry)
            self._pattern_registry = [p for p in self._pattern_registry if p["pattern"] != pattern]
            removed = len(self._pattern_registry) < initial_count

            if removed:
                logger.info("Pattern Removed: pattern=%s", pattern)
                return True
            return False

    def clear_patterns(self) -> None:
        """Clears all pattern rules from the registry."""
        with self._lock:
            self._pattern_registry.clear()
            logger.info("Pattern Registry Cleared")

    def analyze(self, text: str) -> IntentAnalysisResult:
        """Deterministically analyzes text input against registered pattern rules."""
        with self._lock:
            if not text or not text.strip():
                result = IntentAnalysisResult(
                    intent=IntentCategory.UNKNOWN,
                    confidence=IntentConfidence.VERY_LOW,
                    matched_patterns=[],
                    reason="Empty or whitespace input",
                )
                logger.info("Intent Analysis Performed: input=%s, intent=%s, confidence=%s", text, result.intent, result.confidence)
                return result

            clean_text = text if self.config.case_sensitive else text.lower()
            matches: List[Dict[str, Any]] = []

            for rule in self._pattern_registry:
                pat = rule["pattern"]
                is_regex = rule.get("is_regex", False)
                matched = False

                if is_regex:
                    flags = 0 if self.config.case_sensitive else re.IGNORECASE
                    try:
                        if re.search(pat, text, flags=flags):
                            matched = True
                    except re.error:
                        matched = False
                else:
                    pat_target = pat if self.config.case_sensitive else pat.lower()
                    if pat_target in clean_text:
                        matched = True

                if matched:
                    matches.append(rule)

            if not matches:
                result = IntentAnalysisResult(
                    intent=IntentCategory.UNKNOWN,
                    confidence=IntentConfidence.VERY_LOW,
                    matched_patterns=[],
                    reason="No matching pattern found",
                )
                logger.info("Intent Analysis Performed: input=%s, intent=%s, confidence=%s", text, result.intent, result.confidence)
                return result

            # Sort matches by priority descending, then confidence rank descending
            matches.sort(
                key=lambda m: (
                    m.get("priority", 1),
                    CONFIDENCE_RANK.get(m.get("confidence", IntentConfidence.MEDIUM), 3),
                ),
                reverse=True,
            )

            best_match = matches[0]
            matched_patterns = [m["pattern"] for m in matches]

            result = IntentAnalysisResult(
                intent=best_match["intent"],
                confidence=best_match["confidence"],
                matched_patterns=matched_patterns,
                reason=f"Matched pattern '{best_match['pattern']}'",
                metadata=best_match.get("metadata", {}),
            )
            logger.info("Intent Analysis Performed: input=%s, intent=%s, confidence=%s", text, result.intent, result.confidence)
            return result

    def list_patterns(self, intent: Optional[IntentCategory] = None) -> List[Dict[str, Any]]:
        """Lists registered pattern rules, optionally filtered by IntentCategory."""
        with self._lock:
            if intent is not None:
                return [dict(p) for p in self._pattern_registry if p["intent"] == intent]
            return [dict(p) for p in self._pattern_registry]
