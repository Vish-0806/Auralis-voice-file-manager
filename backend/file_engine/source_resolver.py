import os
from typing import Dict, Any
from file_engine.search_engine import search_files
from utils.logger import get_logger

logger = get_logger(__name__)


def resolve_source(target: str) -> Dict[str, Any]:
    """
    Resolves the target file or folder name to a unique path.

    Returns a dictionary with:
    - 'status': 'success', 'disambiguation', or 'error'
    - 'path': Resolved absolute path if status is 'success'
    - 'results': List of matches if status is 'disambiguation'
    - 'message': Description of the result
    """
    if not target:
        return {
            "status": "error",
            "message": "Target name is empty.",
            "error_class": "ValueError",
        }

    # If target is already a valid path on disk, use it directly
    if os.path.exists(target):
        logger.info("Target '%s' resolved directly (exists on disk).", target)
        return {
            "status": "success",
            "path": os.path.abspath(target),
            "message": "Target exists on disk.",
        }

    logger.info("Searching for target: '%s' using search engine.", target)
    results = search_files(target)

    if not results:
        logger.warning("No files found matching target: '%s'", target)
        return {
            "status": "error",
            "message": f"File '{target}' not found.",
            "error_class": "FileNotFoundError",
        }

    if len(results) == 1:
        resolved_path = results[0]["path"]
        logger.info("Target '%s' resolved to unique path: '%s'", target, resolved_path)
        return {
            "status": "success",
            "path": resolved_path,
            "message": "Found exactly one matching file.",
        }

    # Multiple files found
    logger.info("Multiple matches found for target '%s': %d matches.", target, len(results))
    return {
        "status": "disambiguation",
        "message": f"Multiple files found matching '{target}'.",
        "results": results,
    }
