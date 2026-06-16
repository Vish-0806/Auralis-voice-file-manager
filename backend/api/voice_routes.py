"""
Voice API routes for speech-to-text command handling.
Integrates with ai_engine for command parsing and file_engine for execution.
"""

from fastapi import APIRouter, HTTPException
from voice_engine.speech_to_text import listen
from voice_engine.wake_word import detect_wake_word
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action
from voice_engine.text_to_speech import speak as tts_speak
from utils.logger import get_logger
from utils.helpers import format_speak_message

logger = get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/listen")
def handle_voice_command():
    """
    Listen to microphone input and execute recognized command.
    
    Flow:
    1. Capture audio from microphone
    2. Convert speech to text
    3. Detect wake word
    4. Parse command into action and target
    5. Execute action using file engine
    6. Return structured response
    
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
    
    # Step 2: Detect wake word
    wake_result = detect_wake_word(recognized_text)
    
    if not wake_result["activated"]:
        logger.info("Wake word not detected, ignoring input: '%s'", recognized_text)
        return {"status": "ignored", "message": "Wake word not detected"}
    
    logger.info("Wake word detected. Cleaned command: '%s'", wake_result["cleaned_command"])
    command = wake_result["cleaned_command"]
    
    # If the user only said the wake phrase with no trailing command, prompt them
    if not command:
        msg = "How can I help you?"
        logger.info("Wake word detected but no command followed")
        try:
            tts_speak(msg)
        except Exception:
            logger.exception("Failed to speak prompt message")
        return {"status": "awaiting_command", "message": msg}
    
    # Step 3: Parse the command
    logger.info("Parsing recognized text")
    parsed_action = parse_command(command)

    # Handle unknown commands early
    if parsed_action.get("action") == "unknown":
        msg = "Command not recognized"
        try:
            tts_speak(msg)
        except Exception:
            logger.exception("Failed to speak unknown-command message")

        logger.warning("Unknown command: %s", command)
        raise HTTPException(status_code=400, detail=msg)

    # Step 4: Execute the action
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
        speak_msg = format_speak_message(result, parsed_action)

        # Announce result via TTS (best-effort)
        try:
            tts_speak(speak_msg)
        except Exception:
            logger.exception("Failed to speak result message")

    except Exception:
        logger.exception("Error preparing or speaking result message")

    # Step 5: Return structured response
    response = {
        "status": "success",
        "recognized_text": recognized_text,
        "command": command,
        "parsed_action": parsed_action,
        "result": result
    }

    logger.info("Voice command executed successfully: %s", parsed_action.get("action"))
    return response
