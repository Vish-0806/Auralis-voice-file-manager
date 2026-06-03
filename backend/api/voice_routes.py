"""
Voice API routes for speech-to-text command handling.
Integrates with ai_engine for command parsing and file_engine for execution.
"""

from fastapi import APIRouter, HTTPException
from voice_engine.speech_to_text import listen
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action
from voice_engine.text_to_speech import speak as tts_speak
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/listen")
def handle_voice_command():
    """
    Listen to microphone input and execute recognized command.
    
    Flow:
    1. Capture audio from microphone
    2. Convert speech to text
    3. Parse command into action and target
    4. Execute action using file engine
    5. Return structured response
    
    Returns:
        dict: Response containing status, recognized command, parsed action, and result
        
    Raises:
        HTTPException: If speech recognition fails or command execution errors occur
    """
    
    logger.info("Voice command endpoint invoked")
    
    # Step 1: Capture and recognize speech
    recognized_text = listen()
    
    if recognized_text is None:
        logger.warning("Failed to recognize speech")
        raise HTTPException(
            status_code=400,
            detail="Could not recognize speech. Please try again."
        )
    
    # Step 2: Parse the command
    logger.info("Parsing recognized text")
    parsed_action = parse_command(recognized_text)

    # Handle unknown commands early
    if parsed_action.get("action") == "unknown":
        msg = "Command not recognized"
        try:
            tts_speak(msg)
        except Exception:
            logger.exception("Failed to speak unknown-command message")

        logger.warning("Unknown command: %s", recognized_text)
        raise HTTPException(status_code=400, detail=msg)

    # Step 3: Execute the action
    logger.info("Executing parsed action: %s", parsed_action)
    try:
        result = execute_action(parsed_action)
    except Exception as exc:
        logger.exception("Error executing action: %s", exc)
        msg = "Failed to execute command"
        try:
            tts_speak(msg)
        except Exception:
            logger.exception("Failed to speak execution-failure message")
        raise HTTPException(status_code=500, detail=msg)

    # Prepare spoken message (map common responses to user-friendly phrases)
    try:
        lr = result.lower()
        if lr.startswith("opened"):
            speak_msg = result
        elif "created" in lr:
            speak_msg = "Folder created successfully"
        elif "not found" in lr:
            speak_msg = f"{parsed_action.get('target')} not found"
        elif lr == "unknown action":
            speak_msg = "Command not recognized"
        else:
            speak_msg = result

        # Announce result via TTS (best-effort)
        try:
            tts_speak(speak_msg)
        except Exception:
            logger.exception("Failed to speak result message")

    except Exception:
        logger.exception("Error preparing or speaking result message")

    # Step 4: Return structured response
    response = {
        "status": "success",
        "command": recognized_text,
        "parsed_action": parsed_action,
        "result": result
    }

    logger.info("Voice command executed successfully: %s", parsed_action.get("action"))
    return response
