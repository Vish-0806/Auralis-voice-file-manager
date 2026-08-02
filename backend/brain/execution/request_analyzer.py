"""Request Analyzer for the Auralis Brain Execution Engine Subsystem (Phase 12.1).

Responsible for:
- validating incoming requests
- normalizing requests
- identifying request category
- extracting metadata
- estimating complexity

Performs deterministic analysis without making any external AI calls.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional

from brain.execution.exceptions import ExecutionValidationError
from brain.execution.execution_models import ExecutionMode, ExecutionRequest
from brain.execution.interfaces import IRequestAnalyzer


class RequestAnalyzer(IRequestAnalyzer):
    """Deterministic analyzer for validating, normalizing, categorizing, and scoring incoming requests."""

    def validate_request(self, request: Any) -> ExecutionRequest:
        """Validate and convert incoming input into an immutable ExecutionRequest.

        Args:
            request: ExecutionRequest, dict, BrainRequest, or prompt string.

        Returns:
            Validated ExecutionRequest instance.

        Raises:
            ExecutionValidationError: If request is empty or invalid.
        """
        if request is None:
            raise ExecutionValidationError("Request cannot be None")

        if isinstance(request, ExecutionRequest):
            if not request.prompt and not request.metadata:
                raise ExecutionValidationError("ExecutionRequest prompt and metadata cannot both be empty")
            return request

        if isinstance(request, str):
            clean_str = request.strip()
            if not clean_str:
                raise ExecutionValidationError("Prompt string cannot be empty or whitespace only")
            return ExecutionRequest(prompt=clean_str)

        if isinstance(request, dict):
            prompt_val = str(request.get("prompt") or request.get("raw_text") or request.get("query") or "").strip()
            if not prompt_val and not request.get("metadata"):
                raise ExecutionValidationError("Dictionary request must contain a non-empty prompt or metadata")
            return ExecutionRequest(
                request_id=str(request.get("request_id") or request.get("id") or f"req-{hash(prompt_val)}"),
                prompt=prompt_val,
                session_id=request.get("session_id"),
                user_id=request.get("user_id"),
                category=request.get("category"),
                mode=ExecutionMode(request["mode"]) if "mode" in request and request["mode"] in ExecutionMode.__members__ else ExecutionMode.DEFAULT,
                context=request.get("context") or {},
                metadata=request.get("metadata") or {},
            )

        # Support object attributes (e.g. BrainRequest, AssistantRequest)
        if hasattr(request, "raw_text") or hasattr(request, "prompt"):
            prompt_val = str(getattr(request, "raw_text", getattr(request, "prompt", ""))).strip()
            if not prompt_val and not getattr(request, "metadata", None):
                raise ExecutionValidationError("Request object contains no prompt or metadata")
            req_id = getattr(request, "request_id", None) or getattr(request, "id", None)
            sess_id = getattr(request, "session_id", None)
            user_id = getattr(request, "user_id", None)
            return ExecutionRequest(
                request_id=req_id or f"req-{hash(prompt_val)}",
                prompt=prompt_val,
                session_id=sess_id,
                user_id=user_id,
                metadata=getattr(request, "metadata", {}) or {},
            )

        raise ExecutionValidationError(f"Unsupported request type: {type(request).__name__}")

    def normalize_request(self, request: ExecutionRequest) -> ExecutionRequest:
        """Normalize whitespace, capitalization cues, and metadata payload in request."""
        clean_prompt = " ".join(request.prompt.split()) if request.prompt else ""
        category = self.identify_category(request)
        extracted_meta = self.extract_metadata(request)
        merged_meta = {**request.metadata, **extracted_meta}

        return request.model_copy(
            update={
                "prompt": clean_prompt,
                "category": category,
                "metadata": merged_meta,
            }
        )

    def identify_category(self, request: ExecutionRequest) -> str:
        """Determine request category deterministically using intent pattern matching."""
        if request.category:
            return request.category

        text = request.prompt.lower()

        # Security / system command patterns
        if any(kw in text for kw in ["exec ", "run command", "system", "terminal", "kill process", "shutdown", "format drive", "sudo"]):
            return "SYSTEM_COMMAND"

        # File operation patterns
        if any(kw in text for kw in ["file", "directory", "folder", "copy", "move", "delete", "remove", "rename", "list files", "find file"]):
            return "FILE_OPERATION"

        # Workflow / multi-step planning patterns
        if any(kw in text for kw in ["workflow", "plan", "organize", "pipeline", "multi-step", "sequence", "automate"]):
            return "WORKFLOW_PLANNING"

        # AI generation / text / code synthesis patterns
        if any(kw in text for kw in ["generate", "write", "summarize", "explain", "code", "draft", "translate", "reason"]):
            return "AI_GENERATION"

        # Assistant query patterns
        if any(kw in text for kw in ["status", "help", "who", "what", "how", "where", "info", "hello", "hi"]):
            return "ASSISTANT_QUERY"

        return "UNKNOWN"

    def extract_metadata(self, request: ExecutionRequest) -> Dict[str, Any]:
        """Extract deterministic metadata parameters, target paths, and intent hints."""
        metadata: Dict[str, Any] = {}
        prompt = request.prompt

        # Extract file paths (Windows or POSIX style)
        paths = re.findall(r"(?:[a-zA-Z]:[\\/][^\s\"']+|/[^\s\"']+|(?:\.\.?[\\/])?[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)", prompt)
        if paths:
            metadata["extracted_paths"] = paths

        # Extract dangerous flag indicators
        if any(kw in prompt.lower() for kw in ["force", "override", "delete all", "drop table", "remove -rf", "kill -9", "delete"]):
            metadata["is_potentially_destructive"] = True
        else:
            metadata["is_potentially_destructive"] = False

        # Extract complexity markers
        step_count = len(re.split(r";|\n| and then | then ", prompt, flags=re.IGNORECASE))
        metadata["estimated_step_count"] = max(1, step_count)

        return metadata

    def estimate_complexity(self, request: ExecutionRequest) -> str:
        """Score and estimate complexity rating (LOW, MEDIUM, HIGH, CRITICAL)."""
        prompt = request.prompt.lower()
        meta = request.metadata or {}

        if meta.get("is_potentially_destructive") or any(kw in prompt for kw in ["format drive", "drop database", "delete system", "kill -9"]):
            return "CRITICAL"

        step_count = meta.get("estimated_step_count", len(re.split(r";|\n| and then | then ", prompt, flags=re.IGNORECASE)))
        if step_count > 3 or any(kw in prompt for kw in ["workflow", "multi-step", "pipeline", "organize workspace"]):
            return "HIGH"

        if step_count > 1 or any(kw in prompt for kw in ["generate", "summarize", "search", "copy directory", "delete"]):
            return "MEDIUM"

        return "LOW"

    def analyze(self, request: Any) -> ExecutionRequest:
        """Perform full validation, normalization, metadata extraction, and scoring in one call."""
        validated = self.validate_request(request)
        normalized = self.normalize_request(validated)
        complexity = self.estimate_complexity(normalized)

        updated_meta = {**normalized.metadata, "complexity": complexity}
        return normalized.model_copy(update={"metadata": updated_meta})
