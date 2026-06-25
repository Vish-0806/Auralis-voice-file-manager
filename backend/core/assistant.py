"""
Module: backend.core.assistant

Responsibility:
    Acts as the main entry orchestrator for the Auralis AI Operating System Assistant.
    Coordinates requests by connecting gateways, state observers, planners, and dispatchers.

This module SHOULD:
    - Inject IAgentBrain, IMemoryManager, IEventBus, and IOSAdapter in its constructor.
    - Coordinate context gathering, planning, execution dispatching, and response cycles.
    - Expose clean methods for API gateways to invoke operations.
    - Implement lightweight legacy adapters to maintain backward compatibility during refactoring.

This module should NEVER:
    - Execute specific file operations, shell scripts, or databases operations directly (delegates to adapters).
    - Hardcode specific model names or UI layouts.
"""

from typing import Dict, Any, List, Optional
from backend.core.interfaces import IAgentBrain, IOSAdapter
from backend.memory.interfaces import IMemoryManager
from backend.events.interfaces import IEventBus
from backend.events.event_types import SystemEvents
from backend.core.session import SessionManager, UserSession
from backend.core.context import ContextBuilder, SystemContext
from backend.core.state import StateManager, SystemStatus
from backend.core.planner import Planner, ExecutionPlan
from backend.core.dispatcher import ActionDispatcher, ExecutionResult


# ===========================================================================
# Lightweight Legacy Adapters to bridge Core to existing modules
# ===========================================================================

class LegacyAgentBrain(IAgentBrain):
    """Adapts legacy command parsing to the IAgentBrain interface."""
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from ai_engine.command_parser import parse_command
        return parse_command(request)


class LegacyMemoryManager(IMemoryManager):
    """Placeholder legacy memory manager adapter."""
    def get_active_context(self, session_id: str, query: str) -> Dict[str, Any]:
        return {}
    def commit_interaction(self, session_id: str, prompt: str, response: str) -> None:
        pass


class LegacyEventBus(IEventBus):
    """Placeholder legacy event bus adapter."""
    def publish_envelope(self, envelope: Any) -> None:
        pass
    def subscribe(self, topic: str, subscriber: Any) -> None:
        pass
    def unsubscribe(self, topic: str, subscriber: Any) -> None:
        pass


class LegacyOSAdapter(IOSAdapter):
    """Adapts path resolving to the IOSAdapter interface."""
    def execute_shell(self, command: str) -> str:
        return ""
    def resolve_path(self, path: str) -> str:
        from file_engine.source_resolver import resolve_source
        return resolve_source(path)


# ===========================================================================
# Main Orchestrator Definition
# ===========================================================================

class AuralisAssistant:
    """The central coordinator of the Auralis core pipeline, managing the request lifecycle."""
    
    def __init__(self,
                 agent_brain: IAgentBrain,
                 memory_manager: IMemoryManager,
                 event_bus: IEventBus,
                 os_adapter: IOSAdapter) -> None:
        # Dependency Injection of Interfaces
        self.agent_brain: IAgentBrain = agent_brain
        self.memory_manager: IMemoryManager = memory_manager
        self.event_bus: IEventBus = event_bus
        self.os_adapter: IOSAdapter = os_adapter

        # Core Components Initialization
        self.session_manager: SessionManager = SessionManager()
        self.context_builder: ContextBuilder = ContextBuilder(os_adapter)
        self.state_manager: StateManager = StateManager()
        
        # Inject dependencies into Planner and Dispatcher
        self.planner: Planner = Planner(agent_brain, event_bus)
        self.dispatcher: ActionDispatcher = ActionDispatcher(event_bus)

    def process_request(self, session_id: str, request: str) -> Dict[str, Any]:
        """Processes a command request by delegating to parser and execution logic."""
        parsed_action = self.parse_command(request)
        result = self.execute_action(parsed_action)
        return {
            "status": "success",
            "command": request,
            "parsed_action": parsed_action,
            "result": result
        }

    # =======================================================================
    # Legacy Gateway Routing Methods
    # =======================================================================

    def listen_voice(self) -> str:
        """Captures microphone input and converts speech to text."""
        from voice.speech_to_text import listen
        return listen()

    def detect_wake_word(self, text: str) -> Dict[str, Any]:
        """Detects the wake word in the recognized text."""
        from voice.wake_word import detect_wake_word
        return detect_wake_word(text)

    def speak(self, text: str) -> None:
        """Plays speech feedback using text-to-speech."""
        from voice.text_to_speech import speak
        speak(text)

    def get_voice_listener(self) -> Any:
        """Retrieves the continuous listener singleton."""
        from voice.continuous_listener import get_listener
        return get_listener()

    def search_files(self, query: str) -> List[Dict[str, str]]:
        """Searches recursively for files matching the query."""
        from file_engine.search_engine import search_files
        return search_files(query)

    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Retrieves the current pending operation from the state manager."""
        from file_engine.file_operations import get_pending_action
        return get_pending_action()

    def classify_intent(self, command: str) -> str:
        """Classifies the user intent string."""
        from ai_engine.intent_classifier import classify_intent
        return classify_intent(command)

    def parse_command(self, command: str) -> Dict[str, Any]:
        """Parses a text command into action and target parameters."""
        return self.agent_brain.reason(command, {})

    def execute_action(self, parsed_action: Dict[str, Any]) -> Any:
        """Executes a parsed file action using the file engine."""
        from file_engine.file_operations import execute_action
        return execute_action(parsed_action)

    def format_speak_message(self, result: Any, parsed_action: Dict[str, Any]) -> str:
        """Formats the result message for speech playback."""
        from utils.helpers import format_speak_message
        return format_speak_message(result, parsed_action)


# Singleton getter/manager for API and listener gateways
_assistant_instance = None

def get_assistant() -> AuralisAssistant:
    """Retrieves or instantiates the singleton AuralisAssistant orchestrator."""
    global _assistant_instance
    if _assistant_instance is None:
        # Initialize legacy adapters
        brain = LegacyAgentBrain()
        memory = LegacyMemoryManager()
        bus = LegacyEventBus()
        os_adapter = LegacyOSAdapter()
        _assistant_instance = AuralisAssistant(brain, memory, bus, os_adapter)
    return _assistant_instance
