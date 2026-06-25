from fastapi import APIRouter
from pydantic import BaseModel

from core.assistant import get_assistant

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


@router.post("/command")
def handle_command(data: CommandRequest):
    """
    Handles text commands by routing them through the AuralisAssistant orchestrator.
    """
    assistant = get_assistant()
    return assistant.process_request("", data.command)