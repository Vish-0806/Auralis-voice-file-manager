"""Goal interpreter implementation for Auralis.

This module exposes the GoalInterpreter class, which is responsible for
normalizing input, performing keyword and rule parsing, and returning a
structured GoalResult.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Final

from .models import Goal, GoalCategory, GoalConfidence, GoalResult
from .goal_classifier import GoalClassifier
from .goal_registry import GoalRegistry


class GoalInterpreter:
    """Converts natural language user requests into structured goals with confidence scores."""

    def __init__(
        self,
        registry: GoalRegistry | None = None,
        classifier: GoalClassifier | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initializes the GoalInterpreter with registry and classifier.

        Args:
            registry: The GoalRegistry instance. If None, a new one is created.
            classifier: The GoalClassifier instance. If None, a new one is created.
            logger: Optional custom logger for interpreter diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)
        self._registry = registry or GoalRegistry(logger=self._logger)
        self._classifier = classifier or GoalClassifier(logger=self._logger)
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """Configures matching rules/regexes for default goals."""
        self._rules: Final[list[dict[str, Any]]] = [
            {
                "goal_name": "START_CODING",
                "patterns": [
                    r"^start coding\b",
                    r"^coding mode\b",
                    r"^dev mode\b",
                    r"^programming mode\b",
                    r"^start code session\b",
                ],
                "keywords": ["coding", "code", "programming", "ide", "vscode"],
            },
            {
                "goal_name": "STUDY",
                "patterns": [
                    r"^study mode\b",
                    r"^start studying\b",
                    r"^learning mode\b",
                    r"^time to study\b",
                    r"^open study session\b",
                ],
                "keywords": ["study", "studying", "learning", "read", "lecture"],
            },
            {
                "goal_name": "MEETING",
                "patterns": [
                    r"^meeting mode\b",
                    r"^start meeting\b",
                    r"^join meeting\b",
                    r"^join call\b",
                    r"^video call\b",
                ],
                "keywords": ["meeting", "call", "zoom", "teams", "calendar"],
            },
            {
                "goal_name": "ORGANIZE_DOWNLOADS",
                "patterns": [
                    r"^organize downloads\b",
                    r"^clean downloads\b",
                    r"^sort downloads\b",
                    r"^downloads folder organize\b",
                ],
                "keywords": ["organize downloads", "clean downloads", "downloads folder"],
            },
            {
                "goal_name": "CLEAN_WORKSPACE",
                "patterns": [
                    r"^clean workspace\b",
                    r"^tidy workspace\b",
                    r"^tidy up\b",
                    r"^clear workspace\b",
                ],
                "keywords": ["clean workspace", "tidy workspace", "tidy up"],
            },
            {
                "goal_name": "LOCK_COMPUTER",
                "patterns": [
                    r"^lock computer\b",
                    r"^lock pc\b",
                    r"^lock screen\b",
                    r"^lock workstation\b",
                ],
                "keywords": ["lock computer", "lock pc", "lock screen"],
            },
            {
                "goal_name": "OPEN_APPLICATION",
                "patterns": [
                    r"^open (?:application|app)\s+(.+)",
                    r"^launch (?:application|app)\s+(.+)",
                    r"^start (?:application|app)\s+(.+)",
                    r"^run (?:application|app)\s+(.+)",
                    r"^open\s+(.+)",
                    r"^launch\s+(.+)",
                    r"^start\s+(.+)",
                    r"^run\s+(.+)",
                ],
                "keywords": ["open", "launch", "start", "run"],
            },
        ]

    def normalize_input(self, text: str) -> str:
        """Normalizes raw natural language user requests.

        Args:
            text: The raw user input message.

        Returns:
            The normalized text string.
        """
        if not text:
            return ""
        normalized = text.strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.lower()

    def interpret(self, message: str) -> GoalResult:
        """Interprets a user request and identifies their goal.

        Args:
            message: The raw user message.

        Returns:
            A GoalResult representing the identified goal and confidence.
        """
        normalized = self.normalize_input(message)
        self._logger.info("Interpreting user request", extra={"normalized_input": normalized})

        if not normalized:
            unknown_goal = self._registry.get_goal("UNKNOWN")
            return GoalResult(
                goal=unknown_goal,
                confidence=GoalConfidence(score=0.0, rationale="Empty request message."),
                normalized_input="",
            )

        best_match_goal: Goal | None = None
        best_score = 0.0
        best_rationale = "No matching patterns or keywords found."
        extracted_params: dict[str, Any] = {}

        # Evaluate rules
        for rule in self._rules:
            goal_name = rule["goal_name"]
            patterns = rule["patterns"]
            keywords = rule["keywords"]

            # Try pattern (regex) match
            for pattern in patterns:
                match = re.search(pattern, normalized)
                if match:
                    score = 1.0
                    rationale = f"Strong regex pattern match for: {pattern}"

                    # Parameter extraction specifically for OPEN_APPLICATION
                    if goal_name == "OPEN_APPLICATION":
                        # Match on the original message to preserve case
                        orig_match = re.search(pattern, message, re.IGNORECASE)
                        if orig_match and len(orig_match.groups()) > 0:
                            app_name = orig_match.group(1).strip()
                            app_name_clean = re.sub(r"^(?:the|a|an)\s+", "", app_name, flags=re.IGNORECASE)
                            # Skip if it refers to file/folder operations
                            if any(kw in normalized for kw in ["folder", "file", "directory", "document", "shortcut", "macro", "workflow"]):
                                continue
                            # Skip if target contains extensions (looks like a file)
                            if re.search(r"\b\w+\.(?:txt|md|pdf|docx|doc|csv|xlsx|xls|json|yaml|yml|png|jpg|jpeg|gif|mp3|wav|mp4|zip)\b", normalized):
                                continue
                            # Skip if it is a common folder name
                            if app_name_clean.lower() in ["desktop", "downloads", "documents", "pictures", "music", "videos"]:
                                continue
                            extracted_params = {"application": app_name}
                        else:
                            continue

                    if score > best_score:
                        best_score = score
                        best_rationale = rationale
                        best_match_goal = self._registry.get_goal(goal_name)
                        break

            if best_score == 1.0:
                break

            # Try keyword keyword proximity/count match
            if goal_name == "OPEN_APPLICATION":
                # Only allow explicit regex matches for OPEN_APPLICATION to avoid false positives
                continue

            matched_keywords = [kw for kw in keywords if kw in normalized]
            if matched_keywords:
                score = round(0.5 + (0.3 * (len(matched_keywords) / len(keywords))), 2)
                score = min(score, 0.8)
                rationale = f"Keyword match for: {', '.join(matched_keywords)}"

                if score > best_score:
                    best_score = score
                    best_rationale = rationale
                    best_match_goal = self._registry.get_goal(goal_name)

        # Fallback to general text classification if no goal matches or score is too low
        if best_match_goal is None or best_score < 0.2:
            self._logger.debug("Falling back to text classification for unrecognized input")
            fallback_category = self._classifier.classify_text(normalized)
            if fallback_category != GoalCategory.GENERAL:
                best_match_goal = Goal(
                    name="UNKNOWN",
                    category=fallback_category,
                    description="Indeterminate goal, heuristically classified.",
                )
                best_score = 0.3
                best_rationale = f"Heuristically classified category as {fallback_category.value}."
            else:
                unknown_goal = self._registry.get_goal("UNKNOWN")
                best_match_goal = unknown_goal
                best_score = 0.0
                best_rationale = "Request did not match any known goals or categories."

        final_goal = Goal(
            name=best_match_goal.name,
            category=best_match_goal.category,
            description=best_match_goal.description,
            parameters=extracted_params,
        )

        confidence = GoalConfidence(score=best_score, rationale=best_rationale)
        result = GoalResult(
            goal=final_goal,
            confidence=confidence,
            normalized_input=normalized,
        )

        self._logger.info(
            "Request interpreted",
            extra={
                "goal_name": final_goal.name,
                "category": final_goal.category.value,
                "confidence_score": confidence.score,
                "rationale": confidence.rationale,
            },
        )
        return result
