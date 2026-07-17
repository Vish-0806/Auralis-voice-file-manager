"""
Voice API routes for speech-to-text command handling.
Integrates with core.assistant for command parsing and execution.
"""

from fastapi import APIRouter, Depends, HTTPException
from api.assistant_routes import get_assistant_dependency
from core.assistant import AuralisAssistant
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/listen")
def handle_voice_command(assistant: AuralisAssistant = Depends(get_assistant_dependency)):
    """
    Listen to microphone input and execute recognized command.
    
    Flow:
    1. Capture audio from microphone
    2. Convert speech to text
    3. Detect wake word
    4. Parse command into action and target
    5. Execute action using file engine
    6. Return structured response
    """
    logger.info("Voice command endpoint invoked")
    
    # Step 1: Capture and recognize speech
    recognized_text = assistant.listen_voice()
    
    if recognized_text is None:
        logger.warning("Failed to recognize speech")
        raise HTTPException(
            status_code=400,
            detail="Could not recognize speech. Please try again."
        )
    
    # Step 2: Detect wake word
    wake_result = assistant.detect_wake_word(recognized_text)
    
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
            assistant.speak(msg)
        except Exception:
            logger.exception("Failed to speak prompt message")
        return {"status": "awaiting_command", "message": msg}
    
    # Step 3: Parse or handle pending action
    pending = assistant.get_pending_action()
    if pending:
        logger.info("Pending action exists. Checking for voice confirmation/cancellation: '%s'", command)
        intent = assistant.classify_intent(command)
        logger.info("Classified voice intent for pending action: '%s'", intent)
        if intent == "confirm":
            parsed_action = {"action": "confirm", "target": ""}
        elif intent == "cancel":
            parsed_action = {"action": "cancel", "target": ""}
        else:
            logger.warning("Voice command '%s' ignored because a confirmation is pending", command)
            msg = "Action pending. Please say yes or no."
            try:
                assistant.speak(msg)
            except Exception:
                logger.exception("Failed to speak action pending message")
            raise HTTPException(status_code=400, detail=msg)
    else:
        logger.info("Parsing recognized text")
        parsed_action = assistant.parse_command(command)

        # Handle unknown commands early
        if parsed_action.get("action") == "unknown":
            msg = "Command not recognized"
            try:
                assistant.speak(msg)
            except Exception:
                logger.exception("Failed to speak unknown-command message")

            logger.warning("Unknown command: %s", command)
            raise HTTPException(status_code=400, detail=msg)

    # Step 4: Execute the action
    logger.info("Executing parsed action: %s", parsed_action)
    try:
        result = assistant.execute_action(parsed_action)
    except Exception as exc:
        logger.exception("Error executing action: %s", exc)
        msg = "Failed to execute command"
        try:
            assistant.speak(msg)
        except Exception:
            logger.exception("Failed to speak execution-failure message")
        raise HTTPException(status_code=500, detail=msg)

    # Prepare spoken message (map common responses to user-friendly phrases)
    try:
        speak_msg = assistant.format_speak_message(result, parsed_action)

        # Announce result via TTS (best-effort)
        try:
            assistant.speak(speak_msg)
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
