from fastapi import APIRouter
from pydantic import BaseModel

from ai_engine.command_parser import parse_command
from file_engine.file_operations import execute_action

router = APIRouter()

class CommandRequest(BaseModel):
    command: str

@router.post("/command")
def handle_command(data: CommandRequest):

    parsed_action = parse_command(data.command)

    result = execute_action(parsed_action)

    return {
        "status": "success",
        "command": data.command,
        "parsed_action": parsed_action,
        "result": result
    }