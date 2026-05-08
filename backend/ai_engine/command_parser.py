def parse_command(command: str):

    command = command.lower()

    if "open" in command:
        return {
            "action": "open",
            "target": command.replace("open", "").strip()
        }

    elif "delete" in command:
        return {
            "action": "delete",
            "target": command.replace("delete", "").strip()
        }

    elif "create folder" in command:
        return {
            "action": "create_folder",
            "target": command.replace("create folder", "").strip()
        }

    return {
        "action": "unknown",
        "target": command
    }