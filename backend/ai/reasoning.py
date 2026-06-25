"""
Module: backend.ai.reasoning

Responsibility:
    Defines model reasoning strategy patterns (e.g. ReAct loop structure).
    Sequences intermediate thought blocks and execution plans.

This module SHOULD:
    - Define a base ReasoningStrategy class implementing IReasoningStrategy.
    - Provide a ReActStrategy class implementing planning, action, observation loops.
    - Define a ChainOfThoughtStrategy class to handle step-by-step reasoning logs.

This module should NEVER:
    - Execute actions directly (must return requested tool commands to the dispatcher).
    - Import provider-specific SDK libraries.
    - Hardcode capabilities parameters.
"""

from typing import Dict, Any, List, Optional
from backend.ai.interfaces import IReasoningStrategy, ILLMProvider
from backend.ai.models import ToolDefinition, ModelResponse


class ReasoningStrategy(IReasoningStrategy):
    """Base class for all AI reasoning strategies."""
    
    def __init__(self, max_steps: int = 5) -> None:
        self.max_steps: int = max_steps

    def execute_reasoning_loop(self, request: str, provider: ILLMProvider, tools: List[ToolDefinition]) -> ModelResponse:
        """Runs the planning and execution loop using the selected strategy."""
        pass


class ChainOfThoughtStrategy(ReasoningStrategy):
    """Executes step-by-step reasoning to plan actions."""
    
    def execute_reasoning_loop(self, request: str, provider: ILLMProvider, tools: List[ToolDefinition]) -> ModelResponse:
        """Runs a reasoning chain to generate plans before execution."""
        pass


class ReActStrategy(ReasoningStrategy):
    """Executes a Reasoning-Action-Observation loop (ReAct)."""
    
    def execute_reasoning_loop(self, request: str, provider: ILLMProvider, tools: List[ToolDefinition]) -> ModelResponse:
        """Executes the loop: receives observations, plans, and yields tool calls."""
        pass
