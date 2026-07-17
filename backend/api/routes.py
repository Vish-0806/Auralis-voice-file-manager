from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.assistant_routes import get_assistant_dependency
from core.assistant import AuralisAssistant

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


@router.post("/command")
def handle_command(data: CommandRequest, assistant: AuralisAssistant = Depends(get_assistant_dependency)):
    """
    Handles text commands by routing them through the AuralisAssistant orchestrator.
    """
    return assistant.process_request("", data.command)