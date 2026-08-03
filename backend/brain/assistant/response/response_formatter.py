"""Response Formatter implementation for Auralis (Phase 13.6).

Formats response text and metadata into Markdown, Plain Text, or JSON representations without UI logic.
Thread-safe using threading.RLock().
"""

import json
import logging
import re
import threading
from typing import Optional

from brain.assistant.response.exceptions import FormattingError
from brain.assistant.response.interfaces import IResponseFormatter
from brain.assistant.response.models import ResponseFormat, ResponseMetadata

logger = logging.getLogger(__name__)


class ResponseFormatter(IResponseFormatter):
    """Thread-safe content formatter converting raw assistant responses to specified formats."""

    def __init__(self, lock: Optional[threading.RLock] = None) -> None:
        self._lock = lock or threading.RLock()

    def format_content(
        self,
        content: str,
        format_type: ResponseFormat = ResponseFormat.MARKDOWN,
        metadata: Optional[ResponseMetadata] = None,
    ) -> str:
        """Format raw text content into Markdown, Plain Text, or JSON."""
        with self._lock:
            meta = metadata or ResponseMetadata()
            text = content or ""

            try:
                if format_type == ResponseFormat.MARKDOWN:
                    return self._format_markdown(text, meta)
                elif format_type == ResponseFormat.PLAIN_TEXT:
                    return self._format_plain_text(text, meta)
                elif format_type == ResponseFormat.JSON:
                    return self._format_json(text, meta)
                else:
                    return text
            except Exception as exc:
                raise FormattingError(f"Failed to format response content as {format_type}: {exc}") from exc

    def _format_markdown(self, content: str, metadata: ResponseMetadata) -> str:
        formatted = content
        if metadata.citations:
            formatted += "\n\n### References\n" + "\n".join(f"- {c}" for c in metadata.citations)
        return formatted

    def _format_plain_text(self, content: str, metadata: ResponseMetadata) -> str:
        # Strip simple markdown headers and bold/italic markup
        clean_text = re.sub(r"[#*`_~]", "", content)
        if metadata.citations:
            clean_text += "\n\nCitations:\n" + "\n".join(f"- {c}" for c in metadata.citations)
        return clean_text

    def _format_json(self, content: str, metadata: ResponseMetadata) -> str:
        payload = {
            "content": content,
            "citations": metadata.citations,
            "execution_summary": metadata.execution_summary,
            "model": metadata.model_name,
        }
        return json.dumps(payload, indent=2)
