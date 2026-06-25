"""
File search API routes.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Dict
from core.assistant import get_assistant
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/search", response_model=List[Dict[str, str]])
def search_files_endpoint(query: str = Query(..., description="The search term to match filenames")):
    """
    Search recursively for files on Desktop, Documents, and Downloads.
    """
    try:
        logger.info("API request: GET /files/search with query: %s", query)
        assistant = get_assistant()
        results = assistant.search_files(query)
        return results
    except Exception as exc:
        logger.exception("Failed to search files: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search files: {str(exc)}"
        )
