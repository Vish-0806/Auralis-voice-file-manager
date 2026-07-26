"""Activity Predictor analyzing context signals to estimate likely next actions."""

import logging
from typing import List
from memory.proactive.models import PredictionContext

logger = logging.getLogger(__name__)


class ActivityPredictor:
    """Predicts next user desktop operations based on execution histories, routines, and workspace status."""

    def predict_next_actions(self, context: PredictionContext) -> List[str]:
        """Analyzes predictor parameters to extract a list of candidate actions."""
        predictions = []

        # 1. Evaluate execution history + routine sequencing triggers
        if context.executions and context.routines:
            last_execution = context.executions[-1]
            last_action = getattr(last_execution, "action", "")
            for r in context.routines:
                trigger = r.trigger_condition.get("trigger_event", "")
                if trigger == last_action:
                    # Pull sequential actions following the trigger step
                    for step in r.steps:
                        action = step.get("action") or step.get("intent")
                        if action and action != last_action:
                            predictions.append(action)

        # 2. Evaluate workspace intelligence directories status
        ws = context.workspace_info
        if ws.get("project_type") == "python":
            predictions.append("COMPILE_PROJECT")
        if ws.get("repository_type") == "git":
            predictions.append("RUN_COMMAND")

        # 3. Evaluate preferences settings
        if context.preferences.get("preferred_automation") is True:
            predictions.append("OPEN_APPLICATION")

        # 4. Fallback defaults
        if not predictions:
            predictions = ["OPEN_APPLICATION", "RUN_COMMAND"]

        # De-duplicate while preserving insertion order
        unique_predictions = list(dict.fromkeys(predictions))
        logger.info(f"Activity predictor candidates: {unique_predictions}")
        return unique_predictions
