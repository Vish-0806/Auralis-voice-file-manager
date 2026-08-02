"""Intent Validator for the Auralis Intent Resolution Subsystem (Phase 12.2).

Validates intent resolutions for:
- missing required entities
- conflicting parameters
- unsupported parameter combinations
- dangerous requests or destructive system operations
"""

import re
from typing import List, Optional

from brain.execution.intent.intent_models import (
    EntityType,
    IntentCategory,
    IntentContext,
    IntentResolution,
)
from brain.execution.intent.interfaces import IIntentValidator

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bdelete\s+root\b",
    r"\bdelete\s+/[a-z0-9_\-\s]*$",
    r"\bformat\s+[a-z]:\b",
    r"\bdrop\s+database\b",
    r"\bkill\s+-9\s+1\b",
]


class IntentValidator(IIntentValidator):
    """Deterministic validator for IntentResolution model validation and security checking."""

    def validate(
        self,
        resolution: IntentResolution,
        context: Optional[IntentContext] = None,
    ) -> List[str]:
        """Validate intent resolution for missing parameters, conflicts, or dangerous operations.

        Args:
            resolution: IntentResolution object to validate.
            context: Optional IntentContext object.

        Returns:
            List of diagnostic string messages (empty if valid).
        """
        diagnostics: List[str] = []

        if not resolution.primary_intent:
            diagnostics.append("Resolution is missing a primary intent")
            return diagnostics

        intent = resolution.primary_intent
        prompt_clean = intent.normalized_text or intent.raw_prompt.lower()

        # 1. Dangerous request check
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, prompt_clean, flags=re.IGNORECASE):
                diagnostics.append(f"SECURITY_ALERT: Dangerous request pattern detected matching '{pat}'")

        # 2. Missing entity validation
        if intent.category == IntentCategory.FILE_MANAGEMENT:
            if intent.action in ("DELETE_ITEM", "MOVE_ITEM", "COPY_ITEM", "RENAME_ITEM"):
                has_target = any(
                    e.entity_type in (EntityType.FILE, EntityType.FOLDER, EntityType.PATH)
                    for e in resolution.entities
                )
                if not has_target:
                    diagnostics.append(f"Missing required file or folder entity for file management action '{intent.action}'")

        elif intent.category == IntentCategory.APPLICATION_CONTROL:
            if intent.action in ("OPEN_APPLICATION", "CLOSE_APPLICATION", "RESTART_APPLICATION"):
                has_app = any(e.entity_type == EntityType.APPLICATION for e in resolution.entities)
                if not has_app:
                    diagnostics.append(f"Missing required application entity for action '{intent.action}'")

        elif intent.category == IntentCategory.SYSTEM_CONTROL:
            if intent.action == "SET_VOLUME":
                has_num = any(e.entity_type == EntityType.NUMBER for e in resolution.entities)
                if not has_num:
                    diagnostics.append("Missing required volume level number for SET_VOLUME action")

        # 3. Conflicting parameters check
        paths = [e for e in resolution.entities if e.entity_type == EntityType.PATH]
        if len(paths) > 2:
            diagnostics.append(f"Conflicting parameters: Found {len(paths)} path entities in a single operation")

        # 4. Unsupported combinations check
        if intent.category == IntentCategory.DEVICE_CONTROL:
            has_file = any(e.entity_type == EntityType.FILE for e in resolution.entities)
            if has_file:
                diagnostics.append("Unsupported combination: File entity passed to device control operation")

        return diagnostics
