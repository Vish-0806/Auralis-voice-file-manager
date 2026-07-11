"""Planner contracts and keyword-based request analysis for Auralis.

This module implements the core planning boundary only. It converts an
AssistantRequest into a structured ExecutionPlan using lightweight keyword
parsing and simple heuristics. No AI services, file operations, or execution
side effects are performed here.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Final

from brain.goal.goal_interpreter import GoalInterpreter
from brain.goal.models import Goal
from brain.reasoning.reasoning_engine import ReasoningEngine
from brain.reasoning.models import ReasoningResult
from brain.planning.task_planner import TaskPlanner
from .exceptions import ValidationException
from .interfaces import IPlanner
from .intents import Intent
from .models import AssistantRequest, ExecutionPlan as CoreExecutionPlan, SessionContext

ExecutionPlan = CoreExecutionPlan


class Planner(IPlanner):
    """Builds simple execution plans from assistant requests.

    The planner uses only deterministic keyword parsing so it remains fully
    unit-testable and independent from any language model or execution engine.
    """

    SUPPORTED_INTENTS: Final[tuple[Intent, ...]] = (
        Intent.OPEN_FOLDER,
        Intent.OPEN_FILE,
        Intent.SEARCH_FILE,
        Intent.LIST_DIRECTORY,
        Intent.CREATE_FOLDER,
        Intent.DELETE_FOLDER,
        Intent.ORGANIZE_FOLDER,
        Intent.GET_FILE_INFO,
        Intent.OPEN_APPLICATION,
        Intent.CLOSE_APPLICATION,
        Intent.RESTART_APPLICATION,
        Intent.LIST_RUNNING_APPLICATIONS,
        Intent.MINIMIZE_WINDOW,
        Intent.MAXIMIZE_WINDOW,
        Intent.RESTORE_WINDOW,
        Intent.FOCUS_WINDOW,
        Intent.CLOSE_WINDOW,
        Intent.SHOW_DESKTOP,
        Intent.LIST_WINDOWS,
        Intent.SET_VOLUME,
        Intent.MUTE,
        Intent.UNMUTE,
        Intent.SET_BRIGHTNESS,
        Intent.LOCK_PC,
        Intent.SLEEP_PC,
        Intent.SHUTDOWN_PC,
        Intent.RESTART_PC,
        Intent.HIBERNATE_PC,
        Intent.ENABLE_WIFI,
        Intent.DISABLE_WIFI,
        Intent.ENABLE_BLUETOOTH,
        Intent.DISABLE_BLUETOOTH,
        Intent.COPY_SELECTION,
        Intent.PASTE,
        Intent.CLEAR_CLIPBOARD,
        Intent.SHOW_CLIPBOARD,
        Intent.SAVE_CLIPBOARD,
        Intent.COPY_FILE_PATH,
        Intent.TAKE_SCREENSHOT,
        Intent.CAPTURE_WINDOW,
        Intent.CAPTURE_MONITOR,
        Intent.DELAYED_SCREENSHOT,
        Intent.COPY_SCREENSHOT,
        Intent.SAVE_SCREENSHOT,
        Intent.START_RECORDING,
        Intent.STOP_RECORDING,
        Intent.TYPE_TEXT,
        Intent.PRESS_KEY,
        Intent.PRESS_SHORTCUT,
        Intent.MOVE_MOUSE,
        Intent.CLICK_MOUSE,
        Intent.DOUBLE_CLICK,
        Intent.RIGHT_CLICK,
        Intent.SCROLL,
        Intent.DRAG_DROP,
        Intent.RUN_MACRO,
        Intent.RUN_WORKFLOW,
        Intent.LIST_WORKFLOWS,
        Intent.UNKNOWN,
    )

    _FOLDER_NAMES: Final[tuple[str, ...]] = (
        "desktop",
        "downloads",
        "documents",
        "pictures",
        "music",
        "videos",
    )

    _OPEN_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "open folder",
        "open the folder",
        "go to folder",
        "navigate to folder",
        "show folder",
    )

    _OPEN_FILE_HINTS: Final[tuple[str, ...]] = (
        "open file",
        "open the file",
        "open document",
        "open the document",
    )

    _SEARCH_FILE_HINTS: Final[tuple[str, ...]] = (
        "search file",
        "find file",
        "look for file",
        "search for",
        "find",
    )

    _LIST_DIRECTORY_HINTS: Final[tuple[str, ...]] = (
        "list directory",
        "list folder",
        "show directory",
        "show files in",
        "list files in",
        "show contents",
        "list contents",
    )

    _CREATE_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "create folder",
        "create a folder",
        "make folder",
        "make a folder",
        "new folder",
        "create directory",
        "make directory",
    )

    _DELETE_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "delete folder",
        "delete the folder",
        "remove folder",
        "remove the folder",
        "trash folder",
        "discard folder",
    )

    _ORGANIZE_FOLDER_HINTS: Final[tuple[str, ...]] = (
        "organize",
        "clean",
        "sort",
    )

    _GET_FILE_INFO_HINTS: Final[tuple[str, ...]] = (
        "show information about",
        "show info about",
        "file info",
        "folder info",
        "properties of",
        "information about",
        "get info for",
    )

    _OPEN_APP_HINTS: Final[tuple[str, ...]] = (
        "open application ",
        "open app ",
        "launch application ",
        "launch app ",
        "start application ",
        "start app ",
        "run application ",
        "run app ",
        "open ",
        "launch ",
        "start ",
        "run ",
    )

    _CLOSE_APP_HINTS: Final[tuple[str, ...]] = (
        "close application ",
        "close app ",
        "exit application ",
        "exit app ",
        "terminate application ",
        "terminate app ",
        "kill application ",
        "kill app ",
        "stop application ",
        "stop app ",
        "close ",
        "exit ",
        "terminate ",
        "kill ",
        "stop ",
    )

    _RESTART_APP_HINTS: Final[tuple[str, ...]] = (
        "restart application ",
        "restart app ",
        "relaunch application ",
        "relaunch app ",
        "restart ",
        "relaunch ",
    )

    _LIST_RUNNING_APPS_HINTS: Final[tuple[str, ...]] = (
        "list running applications",
        "list running apps",
        "show running applications",
        "show running apps",
        "list active applications",
        "list active apps",
        "show active applications",
        "show active apps",
        "running applications",
        "running apps",
        "list applications",
        "list apps",
        "show applications",
        "show apps",
    )

    _MINIMIZE_WINDOW_HINTS: Final[tuple[str, ...]] = (
        "minimize window ",
        "minimize app ",
        "minimize application ",
        "minimize ",
    )

    _MAXIMIZE_WINDOW_HINTS: Final[tuple[str, ...]] = (
        "maximize window ",
        "maximize app ",
        "maximize application ",
        "maximize ",
    )

    _RESTORE_WINDOW_HINTS: Final[tuple[str, ...]] = (
        "restore window ",
        "restore app ",
        "restore application ",
        "restore ",
    )

    _FOCUS_WINDOW_HINTS: Final[tuple[str, ...]] = (
        "focus window ",
        "focus app ",
        "focus application ",
        "switch to ",
        "focus ",
    )

    _CLOSE_WINDOW_HINTS: Final[tuple[str, ...]] = (
        "close window ",
        "close app ",
        "close application ",
    )

    _SHOW_DESKTOP_HINTS: Final[tuple[str, ...]] = (
        "show desktop",
        "go to desktop",
        "minimize all windows",
        "minimize all",
        "hide all windows",
    )

    _LIST_WINDOWS_HINTS: Final[tuple[str, ...]] = (
        "list open windows",
        "list windows",
        "show open windows",
        "show windows",
    )

    _SET_VOLUME_HINTS: Final[tuple[str, ...]] = (
        "set volume to ",
        "set volume ",
        "increase volume to ",
        "increase volume ",
        "decrease volume to ",
        "decrease volume ",
        "change volume to ",
        "change volume ",
        "volume to ",
        "volume ",
    )

    _SET_BRIGHTNESS_HINTS: Final[tuple[str, ...]] = (
        "set brightness to ",
        "set brightness ",
        "increase brightness to ",
        "increase brightness ",
        "decrease brightness to ",
        "decrease brightness ",
        "brightness to ",
        "brightness ",
    )

    _FILE_EXTENSION_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"\b[^\s<>:\"'|?*]+\.(?:txt|md|pdf|docx|doc|csv|xlsx|xls|json|yaml|yml|png|jpg|jpeg|gif|mp3|wav|mp4|zip)\b",
        re.IGNORECASE,
    )

    _QUOTED_TEXT_PATTERN: Final[re.Pattern[str]] = re.compile(
        r'"([^"]+)"|\'([^\']+)\'',
    )

    def __init__(
        self,
        agent_brain: Any | None = None,
        event_bus: Any | None = None,
        logger: logging.Logger | None = None,
        goal_threshold: float = 0.7,
        goal_interpreter: GoalInterpreter | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        task_planner: TaskPlanner | None = None,
    ) -> None:
        """Initializes the planner.

        Args:
            agent_brain: Retained for compatibility with the current codebase.
            event_bus: Retained for compatibility with the current codebase.
            logger: Optional logger used for planner diagnostics.
            goal_threshold: Configurable minimum confidence threshold for interpreted goals.
            goal_interpreter: Injected GoalInterpreter implementation.
            reasoning_engine: Injected ReasoningEngine implementation.
            task_planner: Injected TaskPlanner implementation.
        """

        self._agent_brain = agent_brain
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)

        # Load threshold from environment variable if present
        env_threshold = os.environ.get("AURALIS_GOAL_THRESHOLD")
        if env_threshold is not None:
            try:
                goal_threshold = float(env_threshold)
            except ValueError:
                self._logger.warning(
                    "Invalid AURALIS_GOAL_THRESHOLD env variable; using default",
                    extra={"value": env_threshold},
                )

        self._goal_threshold = goal_threshold
        self._goal_interpreter = goal_interpreter or GoalInterpreter(logger=self._logger)
        self._reasoning_engine = reasoning_engine or ReasoningEngine(logger=self._logger)
        self._task_planner = task_planner or TaskPlanner(logger=self._logger)

    def _map_goal_to_plan(self, goal: Goal, confidence_score: float) -> ExecutionPlan | None:
        """Maps an interpreted Goal to a core ExecutionPlan.

        Args:
            goal: The interpreted Goal.
            confidence_score: The confidence score from goal interpreter.

        Returns:
            An ExecutionPlan if mapping succeeds, otherwise None.
        """
        if goal.name == "START_CODING":
            return ExecutionPlan(
                intent=Intent.RUN_WORKFLOW,
                target="Start Coding",
                confidence=confidence_score,
            )
        elif goal.name == "STUDY":
            return ExecutionPlan(
                intent=Intent.RUN_WORKFLOW,
                target="Study Mode",
                confidence=confidence_score,
            )
        elif goal.name == "MEETING":
            return ExecutionPlan(
                intent=Intent.RUN_WORKFLOW,
                target="Meeting Mode",
                confidence=confidence_score,
            )
        elif goal.name == "ORGANIZE_DOWNLOADS":
            return ExecutionPlan(
                intent=Intent.ORGANIZE_FOLDER,
                target="Downloads",
                confidence=confidence_score,
            )
        elif goal.name == "CLEAN_WORKSPACE":
            return ExecutionPlan(
                intent=Intent.RUN_WORKFLOW,
                target="Clean Workspace",
                confidence=confidence_score,
            )
        elif goal.name == "LOCK_COMPUTER":
            return ExecutionPlan(
                intent=Intent.LOCK_PC,
                confidence=confidence_score,
            )
        elif goal.name == "OPEN_APPLICATION":
            app_name = goal.parameters.get("application")
            if app_name:
                return ExecutionPlan(
                    intent=Intent.OPEN_APPLICATION,
                    target=app_name,
                    confidence=confidence_score,
                )
        return None

    def create_plan(
        self,
        request: AssistantRequest,
        context: SessionContext | None = None,
    ) -> ExecutionPlan:
        """Creates a structured execution plan from a user request.

        Args:
            request: The incoming assistant request.
            context: Optional session context for future extensibility.

        Returns:
            A validated ExecutionPlan populated with intent, target, and
            confidence metadata.

        Raises:
            ValidationException: If the request is missing a usable message.
        """

        self._validate_request(request)

        # Run Goal Interpreter first
        if self._goal_interpreter is not None:
            try:
                goal_result = self._goal_interpreter.interpret(request.message)
                if (
                    goal_result.confidence.score >= self._goal_threshold
                    and goal_result.goal.name != "UNKNOWN"
                ):
                    # 1. Run the reasoning engine
                    reasoning_result = self._reasoning_engine.reason(goal_result.goal)

                    # 2. Run the dynamic task planner to generate the plan
                    plan = self._task_planner.plan(reasoning_result, confidence=goal_result.confidence.score)

                    # 3. Embed reasoning details in plan parameters
                    plan.parameters["reasoning"] = {
                        "objective": {
                            "title": reasoning_result.objective.title,
                            "description": reasoning_result.objective.description,
                            "target": reasoning_result.objective.target,
                        },
                        "required_capabilities": reasoning_result.required_capabilities,
                        "constraints": [
                            {
                                "name": c.name,
                                "type": c.type,
                                "description": c.description,
                                "satisfied": c.satisfied,
                            }
                            for c in reasoning_result.constraints
                        ],
                        "priority": reasoning_result.priority.value,
                        "estimated_complexity": reasoning_result.estimated_complexity,
                    }

                    self._logger.info(
                        "Goal dynamically planned and reasoned successfully, bypassing existing planner rules",
                        extra={
                            "goal_name": goal_result.goal.name,
                            "category": goal_result.goal.category.value,
                            "confidence": goal_result.confidence.score,
                        },
                    )
                    return plan
            except Exception as exc:
                self._logger.error(
                    "Error executing Goal Interpreter/Planning, falling back to existing planner rules",
                    exc_info=exc,
                )

        normalized_message = self._normalize_text(request.message)
        intent = self._detect_intent(normalized_message)

        folder_name = None
        destination_folder = None
        if intent == Intent.CREATE_FOLDER:
            folder_name, destination_folder = self._extract_folder_info_from_message(request.message)
            target = folder_name
        elif intent == Intent.DELETE_FOLDER:
            folder_name = self._extract_delete_folder_info_from_message(request.message)
            target = folder_name
        elif intent == Intent.TYPE_TEXT:
            orig = request.message
            if orig.lower().startswith("type "):
                target = orig[len("type "):].strip()
            else:
                target = orig
        elif intent == Intent.MOVE_MOUSE:
            import re
            m = re.search(r'\(?\s*(-?\d+)\s*,\s*(-?\d+)\s*\)?', request.message)
            if m:
                target = f"{m.group(1)},{m.group(2)}"
            else:
                target = self._extract_target(normalized_message, intent)
        elif intent == Intent.RUN_MACRO:
            orig = request.message
            val = orig
            if val.lower().startswith("run "):
                val = val[len("run "):]
            if val.lower().endswith(" macro"):
                val = val[:-len(" macro")]
            target = val.strip()
        elif intent == Intent.PRESS_SHORTCUT:
            orig = request.message
            val = orig
            if val.lower().startswith("press "):
                val = val[len("press "):]
            target = val.strip()
        elif intent == Intent.PRESS_KEY:
            orig = request.message
            val = orig
            if val.lower().startswith("press "):
                val = val[len("press "):]
            target = val.strip()
        elif intent == Intent.SCROLL:
            if "down" in normalized_message:
                target = "down"
            elif "up" in normalized_message:
                target = "up"
            else:
                target = self._extract_target(normalized_message, intent)
        elif intent == Intent.RUN_WORKFLOW:
            orig = request.message
            val = orig
            if val.lower().startswith("run workflow "):
                val = val[len("run workflow "):]
            elif val.lower().startswith("start workflow "):
                val = val[len("start workflow "):]
            target = val.strip()
        else:
            target = self._extract_target(normalized_message, intent)

        confidence = self._calculate_confidence(normalized_message, intent, target)

        parameters: dict[str, Any] = {
            "source": request.source,
            "normalized_message": normalized_message,
        }
        if context is not None:
            parameters["session_context"] = context.model_dump()
        if target is not None:
            parameters["target"] = target

        if intent == Intent.CREATE_FOLDER:
            parameters["folder_name"] = folder_name
            parameters["destination_folder"] = destination_folder
        elif intent == Intent.DELETE_FOLDER:
            parameters["folder_name"] = folder_name

        plan = ExecutionPlan(
            intent=intent,
            target=target,
            parameters=parameters,
            confidence=confidence,
        )

        self._logger.debug(
            "Created execution plan",
            extra={
                "intent": intent.value,
                "target": target,
                "confidence": confidence,
            },
        )
        return plan

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """Validates that a plan is structurally ready for downstream use.

        Args:
            plan: The execution plan to validate.

        Returns:
            True when the plan is valid, otherwise False.
        """

        if not isinstance(plan, CoreExecutionPlan):
            return False

        if plan.intent not in self.SUPPORTED_INTENTS:
            return False

        if not 0.0 <= plan.confidence <= 1.0:
            return False

        if not isinstance(plan.parameters, dict):
            return False

        if plan.target is not None and not plan.target.strip():
            return False

        return True

    def _validate_request(self, request: AssistantRequest) -> None:
        """Validates the incoming request object.

        Args:
            request: The assistant request to validate.

        Raises:
            ValidationException: If the request is not usable.
        """

        if not isinstance(request, AssistantRequest):
            raise ValidationException("Request must be an AssistantRequest instance.")

        if not request.message or not request.message.strip():
            raise ValidationException("Request message cannot be empty.")

        if not request.source or not request.source.strip():
            raise ValidationException("Request source cannot be empty.")

    def _normalize_text(self, text: str) -> str:
        """Normalizes request text for deterministic keyword matching.

        Args:
            text: The raw request message.

        Returns:
            A lower-cased, whitespace-normalized string.
        """

        normalized = text.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _detect_intent(self, normalized_message: str) -> Intent:
        """Detects the most likely supported intent.

        Args:
            normalized_message: The normalized request text.

        Returns:
            One of the supported intent labels.
        """

        if self._contains_any(normalized_message, self._CREATE_FOLDER_HINTS):
            return Intent.CREATE_FOLDER

        if self._contains_any(normalized_message, self._DELETE_FOLDER_HINTS):
            return Intent.DELETE_FOLDER

        if self._contains_any(normalized_message, self._ORGANIZE_FOLDER_HINTS):
            return Intent.ORGANIZE_FOLDER

        if self._contains_any(normalized_message, self._GET_FILE_INFO_HINTS):
            return Intent.GET_FILE_INFO

        if self._looks_like_open_folder_request(normalized_message):
            return Intent.OPEN_FOLDER

        if self._looks_like_open_file_request(normalized_message):
            return Intent.OPEN_FILE

        if self._contains_any(normalized_message, self._LIST_WINDOWS_HINTS):
            return Intent.LIST_WINDOWS

        if self._contains_any(normalized_message, self._SHOW_DESKTOP_HINTS):
            return Intent.SHOW_DESKTOP

        if normalized_message in {"mute", "mute system", "mute audio", "mute sound"}:
            return Intent.MUTE

        if normalized_message in {"unmute", "unmute system", "unmute audio", "unmute sound"}:
            return Intent.UNMUTE

        if any(normalized_message.startswith(hint) for hint in self._SET_VOLUME_HINTS):
            return Intent.SET_VOLUME

        if any(normalized_message.startswith(hint) for hint in self._SET_BRIGHTNESS_HINTS):
            return Intent.SET_BRIGHTNESS

        if normalized_message in {"lock my computer", "lock pc", "lock computer", "lock screen", "lock workstation"}:
            return Intent.LOCK_PC

        if normalized_message == "sleep" or normalized_message in {"put the computer to sleep", "put computer to sleep", "put pc to sleep", "sleep computer", "sleep pc"}:
            return Intent.SLEEP_PC

        if normalized_message == "shutdown" or normalized_message in {"shutdown my computer", "shutdown computer", "shutdown pc"}:
            return Intent.SHUTDOWN_PC

        if normalized_message in {"restart", "reboot", "restart my computer", "restart computer", "restart pc", "reboot computer", "reboot pc"}:
            return Intent.RESTART_PC

        if normalized_message == "hibernate" or normalized_message in {"hibernate my computer", "hibernate computer", "hibernate pc"}:
            return Intent.HIBERNATE_PC

        if normalized_message in {"disable wi-fi", "disable wifi", "turn off wi-fi", "turn off wifi", "wifi off"}:
            return Intent.DISABLE_WIFI

        if normalized_message in {"enable wi-fi", "enable wifi", "turn on wi-fi", "turn on wifi", "wifi on"}:
            return Intent.ENABLE_WIFI

        if normalized_message in {"disable bluetooth", "turn off bluetooth", "bluetooth off"}:
            return Intent.DISABLE_BLUETOOTH

        if normalized_message in {"enable bluetooth", "turn on bluetooth", "bluetooth on"}:
            return Intent.ENABLE_BLUETOOTH

        if normalized_message in {"copy selected text", "copy selection", "copy selected"}:
            return Intent.COPY_SELECTION

        if normalized_message in {"paste", "paste clipboard", "paste contents"}:
            return Intent.PASTE

        if normalized_message in {"clear clipboard", "empty clipboard", "clear my clipboard"}:
            return Intent.CLEAR_CLIPBOARD

        if normalized_message in {"show clipboard contents", "show clipboard", "what is on my clipboard", "view clipboard"}:
            return Intent.SHOW_CLIPBOARD

        if normalized_message == "save clipboard" or normalized_message.startswith("save clipboard as ") or normalized_message.startswith("save clipboard to "):
            return Intent.SAVE_CLIPBOARD

        if normalized_message in {"copy the current file path", "copy current file path", "copy file path"}:
            return Intent.COPY_FILE_PATH

        if normalized_message in {"take a screenshot", "take screenshot", "capture screen", "screenshot"}:
            return Intent.TAKE_SCREENSHOT

        if normalized_message in {"capture the active window", "capture active window", "screenshot active window"}:
            return Intent.CAPTURE_WINDOW

        if normalized_message.startswith("capture monitor ") or normalized_message.startswith("capture display ") or normalized_message.startswith("screenshot monitor "):
            return Intent.CAPTURE_MONITOR

        if normalized_message.startswith("take a screenshot in ") or normalized_message.startswith("take screenshot in ") or normalized_message.startswith("screenshot in "):
            return Intent.DELAYED_SCREENSHOT

        if normalized_message in {"copy screenshot to clipboard", "copy screenshot", "copy capture"}:
            return Intent.COPY_SCREENSHOT

        if normalized_message == "save screenshot" or normalized_message.startswith("save screenshot to ") or normalized_message.startswith("save screenshot as "):
            return Intent.SAVE_SCREENSHOT

        if normalized_message in {"start recording screen", "start screen recording", "start recording", "record screen"}:
            return Intent.START_RECORDING

        if normalized_message in {"stop recording screen", "stop screen recording", "stop recording", "stop record"}:
            return Intent.STOP_RECORDING

        if normalized_message.startswith("type "):
            return Intent.TYPE_TEXT

        if normalized_message.startswith("press "):
            shortcut_indicators = {"ctrl", "shift", "alt", "win", "+"}
            if any(indicator in normalized_message for indicator in shortcut_indicators):
                return Intent.PRESS_SHORTCUT
            return Intent.PRESS_KEY

        if normalized_message.startswith("move mouse ") or normalized_message.startswith("move mouse to "):
            return Intent.MOVE_MOUSE

        if normalized_message in {"click", "click mouse", "left click"}:
            return Intent.CLICK_MOUSE

        if normalized_message in {"double click", "double click mouse"}:
            return Intent.DOUBLE_CLICK

        if normalized_message in {"right click", "right click mouse"}:
            return Intent.RIGHT_CLICK

        if normalized_message.startswith("scroll "):
            return Intent.SCROLL

        if normalized_message.startswith("drag ") or normalized_message.startswith("drag and drop "):
            return Intent.DRAG_DROP

        if (normalized_message.startswith("run ") and normalized_message.endswith(" macro")) or "macro" in normalized_message:
            return Intent.RUN_MACRO

        if normalized_message in {"start coding", "study mode", "meeting mode", "movie mode", "clean workspace"} or normalized_message.startswith("run workflow ") or normalized_message.startswith("start workflow "):
            return Intent.RUN_WORKFLOW

        if normalized_message in {"list workflows", "show workflows", "what workflows do you have"}:
            return Intent.LIST_WORKFLOWS

        if any(normalized_message.startswith(hint) for hint in self._MINIMIZE_WINDOW_HINTS):
            return Intent.MINIMIZE_WINDOW

        if any(normalized_message.startswith(hint) for hint in self._MAXIMIZE_WINDOW_HINTS):
            return Intent.MAXIMIZE_WINDOW

        if any(normalized_message.startswith(hint) for hint in self._RESTORE_WINDOW_HINTS):
            return Intent.RESTORE_WINDOW

        if any(normalized_message.startswith(hint) for hint in self._FOCUS_WINDOW_HINTS):
            return Intent.FOCUS_WINDOW

        if normalized_message.startswith("close window ") or normalized_message.startswith("close app ") or normalized_message.startswith("close application "):
            return Intent.CLOSE_WINDOW

        if self._contains_any(normalized_message, self._LIST_RUNNING_APPS_HINTS):
            return Intent.LIST_RUNNING_APPLICATIONS

        if any(normalized_message.startswith(hint) for hint in self._RESTART_APP_HINTS):
            return Intent.RESTART_APPLICATION

        if any(normalized_message.startswith(hint) for hint in self._CLOSE_APP_HINTS):
            target = normalized_message[len("close "):].strip()
            if target in {"calculator", "calc"}:
                return Intent.CLOSE_WINDOW
            return Intent.CLOSE_APPLICATION

        if any(normalized_message.startswith(hint) for hint in self._OPEN_APP_HINTS):
            return Intent.OPEN_APPLICATION

        if self._contains_any(normalized_message, self._LIST_DIRECTORY_HINTS):
            return Intent.LIST_DIRECTORY

        if self._contains_any(normalized_message, self._SEARCH_FILE_HINTS):
            return Intent.SEARCH_FILE

        if self._looks_like_file_request(normalized_message):
            return Intent.OPEN_FILE

        if self._looks_like_directory_request(normalized_message):
            return Intent.LIST_DIRECTORY

        return Intent.UNKNOWN

    def _extract_target(self, normalized_message: str, intent: Intent) -> str | None:
        """Extracts a likely target from the normalized request.

        Args:
            normalized_message: The normalized request text.
            intent: The detected intent.

        Returns:
            A likely file or folder target, or None when no clear target exists.
        """

        quoted_target = self._extract_quoted_text(normalized_message)
        if quoted_target:
            return quoted_target

        explicit_folder = self._extract_folder_name(normalized_message)
        if explicit_folder:
            return explicit_folder

        explicit_file = self._extract_file_name(normalized_message)
        if explicit_file:
            return explicit_file

        if intent in {Intent.OPEN_FOLDER, Intent.LIST_DIRECTORY}:
            return self._extract_tail_after_action(normalized_message)

        if intent == Intent.OPEN_FILE:
            return self._extract_tail_after_action(normalized_message)

        if intent == Intent.LIST_RUNNING_APPLICATIONS:
            return None

        if intent in {Intent.OPEN_APPLICATION, Intent.CLOSE_APPLICATION, Intent.RESTART_APPLICATION}:
            return self._extract_app_name(normalized_message, intent)

        if intent in {
            Intent.MINIMIZE_WINDOW,
            Intent.MAXIMIZE_WINDOW,
            Intent.RESTORE_WINDOW,
            Intent.FOCUS_WINDOW,
            Intent.CLOSE_WINDOW,
        }:
            return self._extract_window_target(normalized_message, intent)

        if intent in {Intent.SHOW_DESKTOP, Intent.LIST_WINDOWS}:
            return None

        if intent in {Intent.SET_VOLUME, Intent.SET_BRIGHTNESS}:
            return self._extract_number(normalized_message)

        if intent in {
            Intent.MUTE,
            Intent.UNMUTE,
            Intent.LOCK_PC,
            Intent.SLEEP_PC,
            Intent.SHUTDOWN_PC,
            Intent.RESTART_PC,
            Intent.HIBERNATE_PC,
            Intent.ENABLE_WIFI,
            Intent.DISABLE_WIFI,
            Intent.ENABLE_BLUETOOTH,
            Intent.DISABLE_BLUETOOTH,
            Intent.COPY_SELECTION,
            Intent.PASTE,
            Intent.CLEAR_CLIPBOARD,
            Intent.SHOW_CLIPBOARD,
            Intent.COPY_FILE_PATH,
            Intent.TAKE_SCREENSHOT,
            Intent.CAPTURE_WINDOW,
            Intent.COPY_SCREENSHOT,
            Intent.START_RECORDING,
            Intent.STOP_RECORDING,
            Intent.CLICK_MOUSE,
            Intent.DOUBLE_CLICK,
            Intent.RIGHT_CLICK,
            Intent.RUN_WORKFLOW,
            Intent.LIST_WORKFLOWS,
        }:
            return None

        if intent in {Intent.CAPTURE_MONITOR, Intent.DELAYED_SCREENSHOT}:
            return self._extract_number(normalized_message)

        if intent == Intent.SAVE_SCREENSHOT:
            for prefix in ("save screenshot to ", "save screenshot as "):
                if normalized_message.startswith(prefix):
                    return normalized_message[len(prefix):].strip()
            return None

        if intent == Intent.SAVE_CLIPBOARD:
            for prefix in ("save clipboard to ", "save clipboard as "):
                if normalized_message.startswith(prefix):
                    val = normalized_message[len(prefix):].strip()
                    if val not in {"a text file", "text file", "file"}:
                        return val
            return None

        if intent == Intent.SEARCH_FILE:
            return self._extract_search_phrase(normalized_message)

        if intent == Intent.CREATE_FOLDER:
            folder_name, _ = self._extract_folder_info_from_message(normalized_message)
            return folder_name

        if intent == Intent.DELETE_FOLDER:
            return self._extract_delete_folder_info_from_message(normalized_message)

        if intent == Intent.GET_FILE_INFO:
            return self._extract_file_info_phrase(normalized_message)

        return None

    def _calculate_confidence(
        self,
        normalized_message: str,
        intent: Intent,
        target: str | None,
    ) -> float:
        """Calculates a confidence score for the detected plan.

        Args:
            normalized_message: The normalized request text.
            intent: The detected intent.
            target: The extracted target, if any.

        Returns:
            A confidence value between 0.0 and 1.0.
        """

        base_scores = {
            Intent.OPEN_FOLDER: 0.72,
            Intent.OPEN_FILE: 0.74,
            Intent.SEARCH_FILE: 0.70,
            Intent.LIST_DIRECTORY: 0.68,
            Intent.CREATE_FOLDER: 0.75,
            Intent.DELETE_FOLDER: 0.75,
            Intent.ORGANIZE_FOLDER: 0.75,
            Intent.OPEN_APPLICATION: 0.75,
            Intent.CLOSE_APPLICATION: 0.75,
            Intent.RESTART_APPLICATION: 0.75,
            Intent.LIST_RUNNING_APPLICATIONS: 0.75,
            Intent.MINIMIZE_WINDOW: 0.75,
            Intent.MAXIMIZE_WINDOW: 0.75,
            Intent.RESTORE_WINDOW: 0.75,
            Intent.FOCUS_WINDOW: 0.75,
            Intent.CLOSE_WINDOW: 0.75,
            Intent.SHOW_DESKTOP: 0.75,
            Intent.LIST_WINDOWS: 0.75,
            Intent.SET_VOLUME: 0.75,
            Intent.MUTE: 0.75,
            Intent.UNMUTE: 0.75,
            Intent.SET_BRIGHTNESS: 0.75,
            Intent.LOCK_PC: 0.75,
            Intent.SLEEP_PC: 0.75,
            Intent.SHUTDOWN_PC: 0.75,
            Intent.RESTART_PC: 0.75,
            Intent.HIBERNATE_PC: 0.75,
            Intent.ENABLE_WIFI: 0.75,
            Intent.DISABLE_WIFI: 0.75,
            Intent.ENABLE_BLUETOOTH: 0.75,
            Intent.DISABLE_BLUETOOTH: 0.75,
            Intent.COPY_SELECTION: 0.75,
            Intent.PASTE: 0.75,
            Intent.CLEAR_CLIPBOARD: 0.75,
            Intent.SHOW_CLIPBOARD: 0.75,
            Intent.SAVE_CLIPBOARD: 0.75,
            Intent.COPY_FILE_PATH: 0.75,
            Intent.TAKE_SCREENSHOT: 0.75,
            Intent.CAPTURE_WINDOW: 0.75,
            Intent.CAPTURE_MONITOR: 0.75,
            Intent.DELAYED_SCREENSHOT: 0.75,
            Intent.COPY_SCREENSHOT: 0.75,
            Intent.SAVE_SCREENSHOT: 0.75,
            Intent.START_RECORDING: 0.75,
            Intent.STOP_RECORDING: 0.75,
            Intent.TYPE_TEXT: 0.75,
            Intent.PRESS_KEY: 0.75,
            Intent.PRESS_SHORTCUT: 0.75,
            Intent.MOVE_MOUSE: 0.75,
            Intent.CLICK_MOUSE: 0.75,
            Intent.DOUBLE_CLICK: 0.75,
            Intent.RIGHT_CLICK: 0.75,
            Intent.SCROLL: 0.75,
            Intent.DRAG_DROP: 0.75,
            Intent.RUN_MACRO: 0.75,
            Intent.RUN_WORKFLOW: 0.75,
            Intent.LIST_WORKFLOWS: 0.75,
            Intent.UNKNOWN: 0.20,
        }
        confidence = base_scores.get(intent, 0.20)

        if target:
            confidence += 0.18

        if self._contains_any(normalized_message, self._FOLDER_NAMES):
            confidence += 0.05

        if self._extract_file_name(normalized_message) is not None:
            confidence += 0.05

        return round(min(confidence, 1.0), 2)

    def _contains_any(self, text: str, phrases: tuple[str, ...]) -> bool:
        """Checks whether any phrase is present in the text."""

        return any(phrase in text for phrase in phrases)

    def _extract_quoted_text(self, text: str) -> str | None:
        """Extracts quoted text from a request."""

        match = self._QUOTED_TEXT_PATTERN.search(text)
        if match is None:
            return None

        quoted = match.group(1) or match.group(2)
        if quoted is None:
            return None

        return quoted.strip()

    def _extract_folder_name(self, text: str) -> str | None:
        """Extracts a common folder name from the request."""

        for folder_name in self._FOLDER_NAMES:
            if re.search(rf"\b{re.escape(folder_name)}\b", text):
                return folder_name.title()
        return None

    def _extract_file_name(self, text: str) -> str | None:
        """Extracts a likely file name from the request."""

        match = self._FILE_EXTENSION_PATTERN.search(text)
        if match is None:
            return None

        return match.group(0).strip()

    def _extract_tail_after_action(self, text: str) -> str | None:
        """Extracts text after a common action phrase.

        Args:
            text: The normalized request text.

        Returns:
            The trailing target text, if any.
        """

        action_patterns = (
            r"(?:open|list|show|find|search|go to|navigate to|look for|browse)\s+(?:the\s+)?(?:folder|file|directory|contents|files)?\s*(?:in|at|from|for)?\s*(.+)$",
            r"(?:open|list|show|find|search)\s+(.+)$",
        )

        for pattern in action_patterns:
            match = re.search(pattern, text)
            if match is None:
                continue

            candidate = match.group(1).strip()
            candidate = re.sub(r"^(?:the|a|an)\s+", "", candidate)
            if candidate:
                return candidate

        return None

    def _extract_search_phrase(self, text: str) -> str | None:
        """Extracts the phrase likely being searched for.

        Args:
            text: The normalized request text.

        Returns:
            The extracted search phrase, if any.
        """

        match = re.search(
            r"(?:search for|find|look for)\s+(?:the\s+)?(.+)$",
            text,
        )
        if match is None:
            return self._extract_tail_after_action(text)

        candidate = match.group(1).strip()
        candidate = re.sub(r"^(?:the|a|an)\s+", "", candidate)
        return candidate or None

    def _looks_like_file_request(self, text: str) -> bool:
        """Checks for obvious file-oriented wording."""

        return "file" in text or self._extract_file_name(text) is not None

    def _looks_like_open_file_request(self, text: str) -> bool:
        """Checks for an explicit open-file request."""

        if self._contains_any(text, self._OPEN_FILE_HINTS):
            return True

        return text.startswith("open ") and self._looks_like_file_request(text)

    def _looks_like_open_folder_request(self, text: str) -> bool:
        """Checks for an explicit open-folder request."""

        if self._contains_any(text, self._OPEN_FOLDER_HINTS):
            return True

        return text.startswith("open ") and self._contains_any(text, self._FOLDER_NAMES)

    def _looks_like_directory_request(self, text: str) -> bool:
        """Checks for obvious directory-oriented wording."""

        return any(keyword in text for keyword in ("folder", "directory", "contents", "files in"))

    def _extract_folder_info_from_message(self, message: str) -> tuple[str | None, str | None]:
        """Extracts case-preserved folder name and destination from the original message."""

        # Pattern 1: Create folder [folder_name] in [destination]
        p1 = re.compile(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:called\s+)?(.+?)(?:\s+(?:in|on|inside|at|into)\s+(.+))?$",
            re.IGNORECASE
        )
        # Pattern 2: Create folder in/on/inside [destination] called [folder_name]
        p2 = re.compile(
            r"(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:in|on|inside|at|into)\s+(.+?)\s+(?:called\s+)?(.+)",
            re.IGNORECASE
        )

        m2 = p2.search(message)
        if m2:
            destination = m2.group(1).strip().strip("\"'")
            folder_name = m2.group(2).strip().strip("\"'")
            return folder_name, destination

        m1 = p1.search(message)
        if m1:
            folder_name = m1.group(1).strip().strip("\"'")
            destination = m1.group(2).strip().strip("\"'") if m1.group(2) else None
            return folder_name, destination

        return None, None

    def _extract_delete_folder_info_from_message(self, message: str) -> str | None:
        """Extracts case-preserved folder name to delete from the original message."""

        p = re.compile(
            r"(?:delete|remove|trash|discard)\s+(?:the\s+)?(?:folder|directory)\s+(.+)",
            re.IGNORECASE
        )
        m = p.search(message)
        if m:
            return m.group(1).strip().strip("\"'")
        return None

    def _extract_file_info_phrase(self, text: str) -> str | None:
        """Extracts the target file name/path from a file information request."""

        # Match "show information about <file>" or "information about <file>"
        match = re.search(
            r"(?:show\s+)?(?:information|info)\s+about\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip().strip("\"'")

        # Match "properties of <file>"
        match_prop = re.search(
            r"properties\s+of\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if match_prop:
            return match_prop.group(1).strip().strip("\"'")

        # Match "get info for <file>"
        match_info = re.search(
            r"(?:get\s+)?info\s+for\s+(.+)$",
            text,
            re.IGNORECASE
        )
        if match_info:
            return match_info.group(1).strip().strip("\"'")

        # Fallback
        return self._extract_tail_after_action(text)

    def _extract_app_name(self, text: str, intent: Intent) -> str | None:
        """Extracts the application name from the request message."""

        if intent == Intent.OPEN_APPLICATION:
            hints = sorted(self._OPEN_APP_HINTS, key=len, reverse=True)
        elif intent == Intent.CLOSE_APPLICATION:
            hints = sorted(self._CLOSE_APP_HINTS, key=len, reverse=True)
        elif intent == Intent.RESTART_APPLICATION:
            hints = sorted(self._RESTART_APP_HINTS, key=len, reverse=True)
        else:
            return None

        for hint in hints:
            if text.startswith(hint):
                app_name = text[len(hint):].strip()
                known_casings = {
                    "chrome": "Chrome",
                    "microsoft edge": "Microsoft Edge",
                    "edge": "Microsoft Edge",
                    "firefox": "Firefox",
                    "vs code": "VS Code",
                    "vscode": "VS Code",
                    "notepad": "Notepad",
                    "calculator": "Calculator",
                    "spotify": "Spotify",
                    "terminal": "Terminal",
                }
                if app_name in known_casings:
                    return known_casings[app_name]
                return app_name.title()

        return text.title()

    def _extract_window_target(self, text: str, intent: Intent) -> str | None:
        """Extracts the target window/app name from the request."""

        if intent == Intent.MINIMIZE_WINDOW:
            hints = sorted(self._MINIMIZE_WINDOW_HINTS, key=len, reverse=True)
        elif intent == Intent.MAXIMIZE_WINDOW:
            hints = sorted(self._MAXIMIZE_WINDOW_HINTS, key=len, reverse=True)
        elif intent == Intent.RESTORE_WINDOW:
            hints = sorted(self._RESTORE_WINDOW_HINTS, key=len, reverse=True)
        elif intent == Intent.FOCUS_WINDOW:
            hints = sorted(self._FOCUS_WINDOW_HINTS, key=len, reverse=True)
        elif intent == Intent.CLOSE_WINDOW:
            hints = ["close window ", "close app ", "close application ", "close "]
        else:
            return None

        for hint in hints:
            if text.startswith(hint):
                target = text[len(hint):].strip()
                known_casings = {
                    "chrome": "Chrome",
                    "microsoft edge": "Microsoft Edge",
                    "edge": "Microsoft Edge",
                    "firefox": "Firefox",
                    "vs code": "VS Code",
                    "vscode": "VS Code",
                    "notepad": "Notepad",
                    "calculator": "Calculator",
                    "spotify": "Spotify",
                    "terminal": "Terminal",
                }
                if target in known_casings:
                    return known_casings[target]
                return target.title()

        return text.title()

    def _extract_number(self, text: str) -> str | None:
        """Extracts a percentage or numeric value from text."""
        match = re.search(r"(\d+)\s*%?", text)
        if match:
            return match.group(0).strip()
        return None


__all__ = ["ExecutionPlan", "Planner"]