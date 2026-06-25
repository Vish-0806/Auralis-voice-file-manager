"""
Module: backend.ai.interfaces

Responsibility:
    Defines the core interface contracts for the Auralis AI subsystem.
    Enforces decoupling between AI workflows and concrete LLM client libraries or models.

This module SHOULD:
    - Declare abstract classes (abc.ABC) representing components of the AI framework.
    - Define protocols for prompt generation, reasoning execution, tool selection, and safety.
    - Utilize type hints referencing the modular AI data models.

This module should NEVER:
    - Include implementations targeting specific providers like OpenAI, Gemini, or Ollama.
    - Implement concrete execution, text generation, or prompt formatting logic.
    - Import external client SDKs (e.g. google-generativeai, openai).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.ai.models import ChatMessage, PromptPayload, ToolDefinition, ModelResponse, SafetyReport


class ILLMProvider(ABC):
    """Abstract interface contract for LLM provider clients (local or cloud)."""
    
    @abstractmethod
    def generate(self, payload: PromptPayload) -> ModelResponse:
        """Executes inference on the underlying LLM using the compiled payload."""
        pass


class IPromptBuilder(ABC):
    """Abstract interface contract for prompt compilation and template managers."""
    
    @abstractmethod
    def compile_prompt(self, messages: List[ChatMessage], tools: List[ToolDefinition]) -> PromptPayload:
        """Compiles conversation history and active tools into a formatted prompt payload."""
        pass


class IContextBuilder(ABC):
    """Abstract interface contract for aggregating environmental state context."""
    
    @abstractmethod
    def merge_environment_context(self, system_context: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assembles OS variables and retrieved semantic memories into a single context payload."""
        pass


class IReasoningStrategy(ABC):
    """Abstract interface contract for structuring LLM reasoning behaviors (e.g. ReAct)."""
    
    @abstractmethod
    def execute_reasoning_loop(self, request: str, provider: ILLMProvider, tools: List[ToolDefinition]) -> ModelResponse:
        """Runs the planning and execution loop using the selected strategy."""
        pass


class ISafetyValidator(ABC):
    """Abstract interface contract for validating LLM generated plans."""
    
    @abstractmethod
    def audit_response(self, response: ModelResponse) -> SafetyReport:
        """Audits generated plans and tool parameters against safety boundary rules."""
        pass


class IToolSelector(ABC):
    """Abstract interface contract for mapping capabilities to tool definitions."""
    
    @abstractmethod
    def get_available_tools(self) -> List[ToolDefinition]:
        """Compiles active capabilities into tool definitions for the LLM context."""
        pass
