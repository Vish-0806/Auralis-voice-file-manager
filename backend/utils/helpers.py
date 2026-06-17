import os

def format_speak_message(result, parsed_action: dict) -> str:
    """
    Format command execution result into a user-friendly spoken response for text-to-speech.
    """
    action = parsed_action.get("action")
    target = parsed_action.get("target", "")

    if action == "organize":
        if isinstance(result, dict):
            moved = result.get("moved_files", 0)
            cats = result.get("categories_created", 0)
            return f"I organized your {target} folder. Moved {moved} files into {cats} categories."
        return f"I organized your {target} folder."

    if action == "search":
        if isinstance(result, str) or not result or (isinstance(result, dict) and result.get("count", 0) == 0):
            return f"I couldn't find any files named {target}."
        elif isinstance(result, dict):
            count = result.get("count", 0)
            if count == 1:
                single_file = result["results"][0]
                filename = single_file.get("name", "")
                filepath = single_file.get("path", "")
                path_lower = filepath.lower()
                if "documents" in path_lower:
                    folder = "Documents"
                elif "downloads" in path_lower:
                    folder = "Downloads"
                elif "desktop" in path_lower:
                    folder = "Desktop"
                else:
                    folder = os.path.basename(os.path.dirname(filepath))
                return f"I found {filename} in {folder}."
            else:
                return f"I found {count} matching files."
        else:
            return f"I couldn't find any files named {target}."

    if not isinstance(result, str):
        return str(result)

    lr = result.lower()
    if lr.startswith("opened"):
        return result
    elif "created" in lr:
        return "Folder created successfully"
    elif "not found" in lr:
        return f"{target} not found"
    elif lr == "unknown action":
        return "Command not recognized"
    else:
        return result
