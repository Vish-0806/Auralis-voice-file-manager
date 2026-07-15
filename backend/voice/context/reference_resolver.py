"""Parses command strings and resolves pronoun, ordinal, and noun references."""

import re
from typing import Set
from utils.logger import get_logger

from voice.context.models import ContextState, ResolutionResult

logger = get_logger(__name__)

# Extensions associated with documents and images
DOCUMENT_EXTENSIONS: Set[str] = {
    ".txt",
    ".pdf",
    ".docx",
    ".doc",
    ".md",
    ".json",
    ".csv",
    ".xlsx",
    ".log",
}
IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"}


class ReferenceResolver:
    """Resolves natural language references to active context items."""

    def resolve(self, command: str, context: ContextState) -> ResolutionResult:
        """Parses a command, replaces references, and identifies ambiguity.

        Args:
            command: Plain text user command.
            context: Current ContextState session data.

        Returns:
            ResolutionResult enclosing the resolved string or clarification request.
        """
        if not command or not command.strip():
            return ResolutionResult(resolved_command="")

        cmd_lower = command.lower().strip()
        resolved_cmd = command

        # 1. Resolve Ordinals ("the first one", "the second one", "the last file/one")
        if "the first one" in cmd_lower:
            if context.current_search_results:
                target = context.current_search_results[0]
                resolved_cmd = self._replace_word(resolved_cmd, "the first one", target)
            else:
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt="I couldn't find any search results to select the first item.",
                )

        if "the second one" in cmd_lower:
            if len(context.current_search_results) >= 2:
                target = context.current_search_results[1]
                resolved_cmd = self._replace_word(resolved_cmd, "the second one", target)
            else:
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt="I found fewer than two search results in context to select from.",
                )

        if "the last file" in cmd_lower or "the last one" in cmd_lower:
            phrase = "the last file" if "the last file" in cmd_lower else "the last one"
            if context.current_search_results:
                target = context.current_search_results[-1]
                resolved_cmd = self._replace_word(resolved_cmd, phrase, target)
            elif context.current_file:
                resolved_cmd = self._replace_word(resolved_cmd, phrase, context.current_file)
            else:
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt="I couldn't find any recent files in context to refer to.",
                )

        # Re-check command after ordinals
        cmd_lower = resolved_cmd.lower()

        # 2. Resolve Specific Nouns ("the folder", "the document", "the image")
        if "the folder" in cmd_lower:
            if context.current_folder:
                resolved_cmd = self._replace_word(resolved_cmd, "the folder", context.current_folder)
            else:
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt="I don't see any active directory in context. Which folder do you mean?",
                )

        if "the document" in cmd_lower:
            # Check if active file is a document
            if context.current_file and self._is_doc(context.current_file):
                resolved_cmd = self._replace_word(resolved_cmd, "the document", context.current_file)
            else:
                # Search search results for documents
                docs = [f for f in context.current_search_results if self._is_doc(f)]
                if len(docs) == 1:
                    resolved_cmd = self._replace_word(resolved_cmd, "the document", docs[0])
                elif len(docs) > 1:
                    return ResolutionResult(
                        resolved_command=command,
                        requires_clarification=True,
                        clarification_prompt=f"I found multiple documents: {', '.join(docs)}. Which one did you mean?",
                    )
                else:
                    return ResolutionResult(
                        resolved_command=command,
                        requires_clarification=True,
                        clarification_prompt="I couldn't find any documents in the active context.",
                    )

        if "the image" in cmd_lower:
            # Check if active file is an image
            if context.current_file and self._is_image(context.current_file):
                resolved_cmd = self._replace_word(resolved_cmd, "the image", context.current_file)
            else:
                # Search search results for images
                imgs = [f for f in context.current_search_results if self._is_image(f)]
                if len(imgs) == 1:
                    resolved_cmd = self._replace_word(resolved_cmd, "the image", imgs[0])
                elif len(imgs) > 1:
                    return ResolutionResult(
                        resolved_command=command,
                        requires_clarification=True,
                        clarification_prompt=f"I found multiple images: {', '.join(imgs)}. Which one did you mean?",
                    )
                else:
                    return ResolutionResult(
                        resolved_command=command,
                        requires_clarification=True,
                        clarification_prompt="I couldn't find any images in the active context.",
                    )

        # Re-check command after nouns
        cmd_lower = resolved_cmd.lower()

        # 3. Resolve General Pronouns ("it", "that", "this", "those")
        pronoun_match = re.search(r"\b(it|that|this|those)\b", cmd_lower)
        if pronoun_match:
            pronoun = pronoun_match.group(1)
            # Check ambiguity: both file and folder are set
            if context.current_file and context.current_folder:
                logger.info("Ambiguity detected for pronoun '%s'", pronoun)
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt=(
                        f"I see both a file ('{context.current_file}') and a folder "
                        f"('{context.current_folder}') in context. Which one did you mean?"
                    ),
                )
            elif context.current_file:
                resolved_cmd = self._replace_word(resolved_cmd, pronoun, context.current_file)
            elif context.current_folder:
                resolved_cmd = self._replace_word(resolved_cmd, pronoun, context.current_folder)
            else:
                return ResolutionResult(
                    resolved_command=command,
                    requires_clarification=True,
                    clarification_prompt="I couldn't resolve what you're referring to. Which file or folder do you mean?",
                )

        return ResolutionResult(resolved_command=resolved_cmd)

    def _replace_word(self, text: str, word: str, replacement: str) -> str:
        """Helper to replace case-insensitively with exact word boundary checks."""
        # Use re.sub to match exact word boundary
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        return pattern.sub(replacement, text)

    def _is_doc(self, filename: str) -> bool:
        """Checks if a filename ends with a document extension."""
        return any(filename.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

    def _is_image(self, filename: str) -> bool:
        """Checks if a filename ends with an image extension."""
        return any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
