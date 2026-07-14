"""Pattern Analyzer for detecting recurring execution sequences."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from memory.models.domain_models import ExecutionHistoryDomain

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes execution history to find repeating subsequences of actions."""

    @staticmethod
    def _create_episodes(executions: List[ExecutionHistoryDomain], gap_seconds: float = 300.0) -> List[List[ExecutionHistoryDomain]]:
        """Groups a sorted list of executions into episodes based on time gap limits."""
        if not executions:
            return []

        # Sort by creation timestamp
        sorted_ex = sorted(executions, key=lambda x: x.created_at)
        episodes: List[List[ExecutionHistoryDomain]] = []
        current_episode: List[ExecutionHistoryDomain] = [sorted_ex[0]]

        for item in sorted_ex[1:]:
            prev_item = current_episode[-1]
            diff = (item.created_at - prev_item.created_at).total_seconds()
            if diff <= gap_seconds:
                current_episode.append(item)
            else:
                episodes.append(current_episode)
                current_episode = [item]

        if current_episode:
            episodes.append(current_episode)

        return episodes

    @staticmethod
    def _to_key(item: ExecutionHistoryDomain) -> Tuple[str, str]:
        """Converts an execution history item into a comparable key tuple (action, parameter_target)."""
        action = item.action
        # Attempt to extract a target identifier (like app name) to specialize patterns
        target = ""
        params = item.input_parameters or {}
        if "target" in params:
            target = str(params["target"])
        elif "application" in params:
            target = str(params["application"])
        return (action, target)

    @classmethod
    def analyze(
        cls,
        executions: List[ExecutionHistoryDomain],
        min_repeats: int = 2,
    ) -> List[Dict[str, Any]]:
        """Finds recurring contiguous action sequences in execution history.

        Args:
            executions: List of execution history records.
            min_repeats: Minimum times a sequence must repeat to be captured.

        Returns:
            List of dictionary pattern structures containing:
              - 'trigger_event': Trigger action name/description.
              - 'action_sequence': Remaining actions in sequence.
              - 'occurrences': Number of times pattern repeated.
              - 'success_rate': Successful executions ratio.
        """
        logger.info(f"Analyzing {len(executions)} execution logs for repeating patterns.")
        # Filter successful or finished executions
        valid_executions = [ex for ex in executions if ex.status == "success"]
        episodes = cls._create_episodes(valid_executions)

        patterns_counts: Dict[Tuple[Tuple[str, str], ...], int] = {}
        patterns_success: Dict[Tuple[Tuple[str, str], ...], List[bool]] = {}

        # Scan for contiguous sequences of length 2 and 3 in each episode
        for episode in episodes:
            if len(episode) < 2:
                continue

            keys = [cls._to_key(item) for item in episode]
            # Use tuple of execution items to trace back values
            items_list = episode

            # Slide window of size L = 2 to 3
            for L in [2, 3]:
                for i in range(len(keys) - L + 1):
                    window_keys = tuple(keys[i : i + L])
                    patterns_counts[window_keys] = patterns_counts.get(window_keys, 0) + 1
                    
                    # Track success status
                    window_success = [items_list[i + k].status == "success" for k in range(L)]
                    patterns_success.setdefault(window_keys, []).extend(window_success)

        results: List[Dict[str, Any]] = []
        for keys, count in patterns_counts.items():
            if count >= min_repeats:
                # First item in sequence is the trigger_event
                trigger_action, trigger_target = keys[0]
                trigger_event = f"{trigger_action}:{trigger_target}" if trigger_target else trigger_action

                # Remaining items are the action_sequence
                action_list = []
                for action, target in keys[1:]:
                    action_list.append({
                        "action": action,
                        "input_parameters": {"target": target} if target else {},
                    })
                action_sequence = {"steps": action_list}

                success_list = patterns_success.get(keys, [True])
                success_rate = sum(success_list) / len(success_list)

                results.append({
                    "trigger_event": trigger_event,
                    "action_sequence": action_sequence,
                    "occurrences": count,
                    "success_rate": success_rate,
                    "total_sessions": len(episodes),
                })

        # Sort patterns by frequency (occurrences) descending
        results.sort(key=lambda x: x["occurrences"], reverse=True)
        return results
