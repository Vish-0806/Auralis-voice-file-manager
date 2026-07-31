"""DefaultToolParser implementation for provider-independent tool call payload parsing (Phase 10.4).

Parses raw completion response payloads, dictionaries, and JSON strings into ToolCall models.
Validates payload structure and raises ToolParsingError on malformed inputs.
"""

import json
import uuid
import logging
from typing import Any, Dict, List

from brain.ai.ai_models import ToolCall, ToolCategory
from brain.ai.tools.exceptions import ToolParsingError
from brain.ai.tools.interfaces import ToolParserInterface

logger = logging.getLogger(__name__)


class DefaultToolParser(ToolParserInterface):
    """Parses raw provider tool call payloads into validated ToolCall objects."""

    def parse_tool_calls(self, payload: Any) -> List[ToolCall]:
        """Parse raw payload or list of tool calls into a list of ToolCall models.

        Args:
            payload: Raw API response dict, list of tool call dicts, or ToolCall object(s).

        Returns:
            List of parsed ToolCall objects.

        Raises:
            ToolParsingError: If payload cannot be parsed or is malformed.
        """
        if payload is None:
            return []

        if isinstance(payload, ToolCall):
            return [payload]

        if isinstance(payload, list):
            results: List[ToolCall] = []
            for item in payload:
                results.append(self.parse_single_call(item))
            return results

        if isinstance(payload, dict):
            # 1. Check if payload is a raw completion response dict containing choices -> message -> tool_calls
            if "choices" in payload and isinstance(payload["choices"], list) and payload["choices"]:
                msg = payload["choices"][0].get("message", {})
                raw_calls = msg.get("tool_calls", [])
                return [self.parse_single_call(call) for call in raw_calls]

            # 2. Check if payload contains top-level tool_calls array
            if "tool_calls" in payload and isinstance(payload["tool_calls"], list):
                return [self.parse_single_call(call) for call in payload["tool_calls"]]

            # 3. Otherwise try parsing payload as a single tool call dictionary
            return [self.parse_single_call(payload)]

        if isinstance(payload, str):
            try:
                data = json.loads(payload)
                return self.parse_tool_calls(data)
            except Exception as exc:
                raise ToolParsingError(f"Failed to parse JSON string payload: {exc}") from exc

        raise ToolParsingError(f"Unsupported tool call payload type '{type(payload).__name__}'.")

    def parse_single_call(self, raw_call: Any) -> ToolCall:
        """Parse a single raw tool call payload into a ToolCall model.

        Args:
            raw_call: ToolCall instance, dict, or JSON string.

        Returns:
            Validated ToolCall object.

        Raises:
            ToolParsingError: If call payload is malformed or missing required fields.
        """
        if isinstance(raw_call, ToolCall):
            return raw_call

        if isinstance(raw_call, str):
            try:
                raw_call = json.loads(raw_call)
            except Exception as exc:
                raise ToolParsingError(f"Invalid JSON string in tool call: {exc}") from exc

        if not isinstance(raw_call, dict):
            raise ToolParsingError(f"Tool call item must be a dictionary, got '{type(raw_call).__name__}'.")

        call_id = raw_call.get("id") or raw_call.get("call_id") or f"call-{uuid.uuid4().hex[:8]}"

        # Handle OpenAI / Groq tool call structure: {"id": "...", "function": {"name": "...", "arguments": "..."}}
        if "function" in raw_call and isinstance(raw_call["function"], dict):
            func = raw_call["function"]
            tool_name = func.get("name")
            raw_args = func.get("arguments", {})
        else:
            tool_name = raw_call.get("tool_name") or raw_call.get("name")
            raw_args = raw_call.get("arguments") or raw_call.get("args") or {}

        if not tool_name or not isinstance(tool_name, str):
            raise ToolParsingError("Tool call dictionary missing required 'tool_name' or 'function.name' string.")

        # Parse arguments dictionary
        args_dict: Dict[str, Any] = {}
        if isinstance(raw_args, str):
            if raw_args.strip():
                try:
                    parsed_args = json.loads(raw_args)
                    if isinstance(parsed_args, dict):
                        args_dict = parsed_args
                    else:
                        args_dict = {"raw": parsed_args}
                except Exception as exc:
                    logger.warning(f"Could not parse tool call arguments as JSON: {exc}. Storing raw string.")
                    args_dict = {"raw": raw_args}
        elif isinstance(raw_args, dict):
            args_dict = raw_args

        # Category mapping
        cat_raw = raw_call.get("category", "filesystem")
        cat_enum = self._map_category(str(cat_raw))

        return ToolCall(
            call_id=str(call_id),
            tool_name=str(tool_name),
            arguments=args_dict,
            category=cat_enum,
        )

    def _map_category(self, cat_str: str) -> ToolCategory:
        """Map raw category string to ToolCategory enum value."""
        clean = cat_str.lower().strip()
        cat_map = {cat.value: cat for cat in ToolCategory}
        return cat_map.get(clean, ToolCategory.FILESYSTEM)
