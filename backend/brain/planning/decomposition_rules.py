"""Decomposition rules engine mapping goals to sub-objectives in Auralis."""

from __future__ import annotations

import logging
from brain.reasoning.models import Objective, ReasoningResult
from .objective_graph import ObjectiveNode, ObjectiveGraph


class DecompositionRules:
    """Evaluates rules to decompose complex ReasoningResults into sub-objectives."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes DecompositionRules.

        Args:
            logger: Optional custom logger.
        """
        self._logger = logger or logging.getLogger(__name__)

    def decompose(self, reasoning: ReasoningResult) -> ObjectiveGraph:
        """Applies decomposition rules on reasoning inputs.

        Args:
            reasoning: ReasoningResult structure to decompose.

        Returns:
            An ObjectiveGraph containing sub-objectives and dependencies.
        """
        goal_name = reasoning.goal_name.upper()
        nodes: dict[str, ObjectiveNode] = {}

        # 1. Build preparation nodes for unsatisfied constraints
        prep_node_ids = []
        for constraint in reasoning.constraints:
            if not constraint.satisfied:
                if constraint.type == "internet":
                    node_id = "prep_enable_wifi"
                    nodes[node_id] = ObjectiveNode(
                        id=node_id,
                        goal_name="PREP_WIFI",
                        objective=Objective(
                            title="Enable Host WiFi Connection",
                            description="Remediate network offline status.",
                        ),
                    )
                    prep_node_ids.append(node_id)
                elif constraint.type == "file_system" and goal_name == "ORGANIZE_DOWNLOADS":
                    node_id = "prep_create_downloads"
                    nodes[node_id] = ObjectiveNode(
                        id=node_id,
                        goal_name="PREP_CREATE_DOWNLOADS",
                        objective=Objective(
                            title="Create Downloads Folder",
                            description="Create Downloads directory on system.",
                        ),
                    )
                    prep_node_ids.append(node_id)

        # 2. Decompose root goal into sub-objectives
        action_nodes: list[ObjectiveNode] = []
        if goal_name == "START_CODING":
            action_nodes = [
                ObjectiveNode(
                    id="step_launch_vscode",
                    goal_name="LAUNCH_VSCODE",
                    objective=Objective(
                        title="Launch Visual Studio Code",
                        description="Start the VS Code IDE workspace.",
                    ),
                ),
                ObjectiveNode(
                    id="step_launch_terminal",
                    goal_name="LAUNCH_TERMINAL",
                    objective=Objective(
                        title="Launch Terminal shell",
                        description="Start default terminal shell interface.",
                    ),
                    dependencies=["step_launch_vscode"],
                ),
                ObjectiveNode(
                    id="step_set_volume",
                    goal_name="SET_VOLUME",
                    objective=Objective(
                        title="Set Quiet Volume",
                        description="Adjust system audio volume level to 30.",
                    ),
                    dependencies=["step_launch_terminal"],
                ),
            ]
            root_id = "step_set_volume"

        elif goal_name == "STUDY":
            action_nodes = [
                ObjectiveNode(
                    id="step_launch_browser",
                    goal_name="LAUNCH_BROWSER",
                    objective=Objective(
                        title="Launch Browser",
                        description="Start default browser application.",
                    ),
                ),
                ObjectiveNode(
                    id="step_mute_sys",
                    goal_name="MUTE",
                    objective=Objective(
                        title="Mute System Audio",
                        description="Mute active system sound outputs.",
                    ),
                ),
            ]
            # Since STUDY doesn't have custom dependencies between browser & mute,
            # we can pick browser as root (mute depends on nothing).
            root_id = "step_launch_browser"

        elif goal_name == "MEETING":
            action_nodes = [
                ObjectiveNode(
                    id="step_launch_notepad",
                    goal_name="LAUNCH_NOTEPAD",
                    objective=Objective(
                        title="Launch Notepad",
                        description="Open basic note application window.",
                    ),
                ),
                ObjectiveNode(
                    id="step_mute_sys",
                    goal_name="MUTE",
                    objective=Objective(
                        title="Mute System Audio",
                        description="Mute sound volume outputs.",
                    ),
                ),
                ObjectiveNode(
                    id="step_show_desktop",
                    goal_name="SHOW_DESKTOP",
                    objective=Objective(
                        title="Show Desktop Workspace",
                        description="Minimize windows to display desktop background.",
                    ),
                    dependencies=["step_launch_notepad", "step_mute_sys"],
                ),
            ]
            root_id = "step_show_desktop"

        elif goal_name == "ORGANIZE_DOWNLOADS":
            action_nodes = [
                ObjectiveNode(
                    id="step_organize_downloads",
                    goal_name="ORGANIZE_DOWNLOADS",
                    objective=reasoning.objective,
                )
            ]
            root_id = "step_organize_downloads"

        elif goal_name == "CLEAN_WORKSPACE":
            action_nodes = [
                ObjectiveNode(
                    id="step_close_chrome",
                    goal_name="CLOSE_CHROME",
                    objective=Objective(
                        title="Close Google Chrome",
                        description="Terminate active Chrome applications.",
                    ),
                ),
                ObjectiveNode(
                    id="step_close_vscode",
                    goal_name="CLOSE_VSCODE",
                    objective=Objective(
                        title="Close VS Code",
                        description="Terminate active VS Code workspaces.",
                    ),
                ),
                ObjectiveNode(
                    id="step_show_desktop",
                    goal_name="SHOW_DESKTOP",
                    objective=Objective(
                        title="Show Desktop Workspace",
                        description="Display clean desktop workspace state.",
                    ),
                    dependencies=["step_close_chrome", "step_close_vscode"],
                ),
            ]
            root_id = "step_show_desktop"

        elif goal_name == "OPEN_APPLICATION":
            root_id = "step_open_app"
            action_nodes = [
                ObjectiveNode(
                    id=root_id,
                    goal_name="OPEN_APPLICATION",
                    objective=reasoning.objective,
                )
            ]

        elif goal_name == "LOCK_COMPUTER":
            root_id = "step_lock_pc"
            action_nodes = [
                ObjectiveNode(
                    id=root_id,
                    goal_name="LOCK_COMPUTER",
                    objective=reasoning.objective,
                )
            ]

        else:
            root_id = "step_fallback"
            action_nodes = [
                ObjectiveNode(
                    id=root_id,
                    goal_name="FALLBACK",
                    objective=reasoning.objective,
                )
            ]

        # Add prep dependencies to all action nodes
        for node in action_nodes:
            if prep_node_ids:
                node.dependencies.extend(prep_node_ids)
            nodes[node.id] = node

        # Ensure prep nodes are registered in the graph map
        for prep_id in prep_node_ids:
            if prep_id not in nodes:
                # prep nodes must be mapped in nodes dict
                pass

        # If a single-step goal with no dependencies, root is the single node
        if len(nodes) == 1:
            root_id = list(nodes.keys())[0]

        return ObjectiveGraph(root_id=root_id, nodes=nodes)
