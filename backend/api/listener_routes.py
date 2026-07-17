"""
Listener API routes to manage the continuous voice listener singleton.
"""

from fastapi import APIRouter, HTTPException, status
from core.assistant import get_assistant
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/listener", tags=["listener"])


@router.post("/start")
def start_listener():
    """
    Start the continuous listener in a background thread if it is not already running.
    """
    try:
        assistant = get_assistant()
        listener = assistant.get_voice_listener()
        if listener.is_running:
            logger.info("Request to start listener ignored: already running")
            return {
                "status": "already_running",
                "message": "Listener is already running"
            }

        listener.start(run_in_thread=True)
        return {
            "status": "started",
            "message": "Listener started successfully"
        }
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Failed to start continuous listener: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start listener: {str(exc)}"
        )


@router.post("/stop")
def stop_listener():
    """
    Stop the continuous listener if it is running.
    """
    try:
        assistant = get_assistant()
        listener = assistant.get_voice_listener()
        if not listener.is_running:
            logger.info("Request to stop listener ignored: not running")
            return {
                "status": "not_running",
                "message": "Listener is not running"
            }

        listener.stop()
        return {
            "status": "stopped",
            "message": "Listener stopped successfully"
        }
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Failed to stop continuous listener: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop listener: {str(exc)}"
        )


@router.get("/status")
def get_listener_status():
    """
    Get the current status of the continuous listener.
    """
    try:
        assistant = get_assistant()
        listener = assistant.get_voice_listener()
        is_running = listener.is_running
        return {
            "running": is_running,
            "status": "running" if is_running else "stopped"
        }
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc)
        )
