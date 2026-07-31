"""DefaultGoalAnalyzer implementation for rule-based user request goal analysis (Phase 10.6).

Normalizes user requests, extracts intent goals, identifies constraints, and determines
required tool capabilities using deterministic rule-based analysis without LLM calls.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional

from brain.ai.planning.exceptions import GoalAnalysisError
from brain.ai.planning.interfaces import GoalAnalyzerInterface
from brain.ai.planning.planning_models import PlanningGoal

logger = logging.getLogger(__name__)


class DefaultGoalAnalyzer(GoalAnalyzerInterface):
    """Deterministic, rule-based GoalAnalyzer implementation."""

    CAPABILITY_KEYWORDS: Dict[str, List[str]] = {
        "filesystem": ["file", "files", "folder", "directory", "move", "copy", "organize", "delete", "read", "list"],
        "memory": ["remember", "memory", "preference", "preferences", "recall", "store", "pinned"],
        "automation": ["automate", "schedule", "routine", "cron", "workflow", "script"],
        "voice": ["speak", "voice", "audio", "say", "speech", "listen"],
        "planner": ["plan", "decompose", "steps", "strategy"],
        "execution": ["run", "execute", "cmd", "process"],
    }

    CONSTRAINT_PATTERNS: Dict[str, List[str]] = {
        "read_only": ["read-only", "don't modify", "dry run", "dry_run", "preview"],
        "safety_strict": ["safe", "careful", "confirm", "confirmation"],
        "timeout": ["fast", "quick", "timeout"],
    }

    def analyze_goal(
        self,
        user_request: str,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> PlanningGoal:
        """Normalize user request and extract goal, constraints, and required capabilities.

        Args:
            user_request: Raw user prompt string.
            constraints: Optional pre-existing constraints dictionary.

        Returns:
            PlanningGoal model instance.

        Raises:
            GoalAnalysisError: If request is empty or whitespace-only.
        """
        if not user_request or not user_request.strip():
            raise GoalAnalysisError("Cannot analyze empty or whitespace-only user request.")

        try:
            # 1. Normalize text
            normalized = self._normalize_text(user_request)

            # 2. Extract capabilities
            capabilities = self._extract_capabilities(normalized)

            # 3. Extract constraints
            extracted_constraints = self._extract_constraints(normalized)

            if constraints:
                extracted_constraints.update(constraints)

            goal_id = f"goal-{uuid.uuid4().hex[:8]}"

            return PlanningGoal(
                goal_id=goal_id,
                raw_text=user_request,
                normalized_goal=normalized,
                constraints=extracted_constraints,
                required_capabilities=capabilities,
                metadata={
                    "analyzer": "DefaultGoalAnalyzer",
                    "capability_count": len(capabilities),
                },
            )

        except Exception as exc:
            if isinstance(exc, GoalAnalysisError):
                raise
            raise GoalAnalysisError(f"Failed to analyze goal: {exc}") from exc

    def _normalize_text(self, text: str) -> str:
        """Strip extra whitespace and normalize text."""
        return " ".join(text.strip().split())

    def _extract_capabilities(self, text: str) -> List[str]:
        """Match query terms against CAPABILITY_KEYWORDS map."""
        text_lower = text.lower()
        matched: List[str] = []

        for cap, keywords in self.CAPABILITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                matched.append(cap)

        # Default capability if none matched
        if not matched:
            matched.append("filesystem")

        return matched

    def _extract_constraints(self, text: str) -> Dict[str, Any]:
        """Match query patterns against CONSTRAINT_PATTERNS map."""
        text_lower = text.lower()
        detected: Dict[str, Any] = {}

        for constraint_name, patterns in self.CONSTRAINT_PATTERNS.items():
            if any(pat in text_lower for pat in patterns):
                detected[constraint_name] = True

        return detected
