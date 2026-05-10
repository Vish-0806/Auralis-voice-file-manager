"""
Voice API routes for speech-to-text command handling.
Integrates with ai_engine for command parsing and file_engine for execution.
"""

from fastapi import APIRouter, HTTPException
from voice_engine.speech_to_text import listen
from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action
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
    logger.info("Executing action")
    parsed_action = parse_command(recognized_text)
    
    # Step 3: Execute the action
    result = execute_action(parsed_action)
    
    # Step 4: Return structured response
    response = {
        "status": "success",
        "command": recognized_text,
        "parsed_action": parsed_action,
        "result": result
    }
    
    logger.info(f"Voice command executed successfully: {parsed_action['action']}")
    return response
