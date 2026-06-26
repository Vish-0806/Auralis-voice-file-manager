import os
import shutil
from file_engine.search_engine import search_files

HOME_DIR = os.path.expanduser("~")

SUPPORTED_LOCATIONS = {
    "desktop",
    "downloads",
    "documents",
    "pictures",
    "music",
    "videos",
}

COMMON_FOLDERS = {
    "desktop": os.path.join(HOME_DIR, "Desktop"),
    "downloads": os.path.join(HOME_DIR, "Downloads"),
    "documents": os.path.join(HOME_DIR, "Documents"),
    "pictures": os.path.join(HOME_DIR, "Pictures"),
    "music": os.path.join(HOME_DIR, "Music"),
    "videos": os.path.join(HOME_DIR, "Videos"),
}


_pending_action = None


def set_pending_action(action_data):
    global _pending_action
    _pending_action = action_data


def get_pending_action():
    return _pending_action


def get_target_path(target):

    target = target.lower()

    # Check common system folders
    if target in COMMON_FOLDERS:
        return COMMON_FOLDERS[target]

    # Default fallback
    return os.path.join(HOME_DIR, target)


def get_location_path(location):
    if not location:
        return HOME_DIR

    location = location.lower()
    if location in SUPPORTED_LOCATIONS:
        return COMMON_FOLDERS[location]

    return HOME_DIR


def execute_action(action_data):

    action = action_data["action"]
    target = action_data["target"]
    location = action_data.get("location", "")

    path = get_target_path(target)
    if action == "create_folder" and location:
        path = os.path.join(get_location_path(location), target)

    try:

        # OPEN
        if action == "open":

            if os.path.exists(path):
                os.startfile(path)
                return f"Opened {target}"

            return f"{target} not found"

        # CREATE FOLDER
        elif action == "create_folder":

            os.makedirs(path, exist_ok=True)

            return f"Folder '{target}' created"

        # DELETE
        elif action == "delete":
            resolved_path = action_data.get("resolved_source_path")
            if resolved_path:
                resolution = {
                    "status": "success",
                    "path": resolved_path
                }
            else:
                from file_engine.source_resolver import resolve_source
                resolution = resolve_source(target)

            if resolution["status"] == "success":
                path_to_delete = resolution["path"]
                if not action_data.get("confirmed"):
                    pending_data = action_data.copy()
                    pending_data["resolved_source_path"] = path_to_delete
                    set_pending_action(pending_data)
                    return {
                        "status": "pending_confirmation",
                        "message": f"Are you sure you want to delete {os.path.basename(path_to_delete)}?",
                        "pending_action": pending_data
                    }

                if os.path.exists(path_to_delete):
                    if os.path.isfile(path_to_delete):
                        os.remove(path_to_delete)
                    elif os.path.isdir(path_to_delete):
                        shutil.rmtree(path_to_delete)
                    return f"{path_to_delete} deleted"

                return f"{os.path.basename(path_to_delete)} not found"
            else:
                if resolution.get("status") == "error":
                    return f"{target} not found"
                return resolution

        # SEARCH
        elif action == "search":
            results = search_files(target)
            if not results:
                return f"No files found matching '{target}'"
            return {
                "count": len(results),
                "results": results
            }

        # ORGANIZE
        elif action == "organize":
            if not os.path.exists(path) or not os.path.isdir(path):
                return f"Directory '{target}' not found"

            if not action_data.get("confirmed"):
                set_pending_action(action_data)
                return {
                    "status": "pending_confirmation",
                    "message": f"Are you sure you want to organize {target}?",
                    "pending_action": action_data
                }

            from file_engine.organizer import organize_directory
            summary = organize_directory(path)
            return f"Successfully organized {target.title()} folder. Moved {summary['moved_files']} files into {summary['categories_created']} categories."

        # CONFIRM
        elif action == "confirm":
            pending = get_pending_action()
            if not pending:
                return "No action pending confirmation"
            set_pending_action(None)
            pending["confirmed"] = True
            return execute_action(pending)

        # CANCEL
        elif action == "cancel":
            pending = get_pending_action()
            if not pending:
                return "No action pending confirmation"
            set_pending_action(None)
            return "Action cancelled"

        # MOVE
        elif action == "move":
            destination = action_data.get("destination", "")
            if not destination:
                return "Destination not specified"

            resolved_path = action_data.get("resolved_source_path")
            if resolved_path:
                resolution = {
                    "status": "success",
                    "path": resolved_path
                }
            else:
                from file_engine.source_resolver import resolve_source
                resolution = resolve_source(target)

            if resolution["status"] == "success":
                if not action_data.get("confirmed"):
                    pending_data = action_data.copy()
                    pending_data["resolved_source_path"] = resolution["path"]
                    set_pending_action(pending_data)
                    filename = os.path.basename(resolution["path"])
                    return {
                        "status": "pending_confirmation",
                        "message": f"Are you sure you want to move {filename} to {destination.title()}?",
                        "pending_action": pending_data
                    }

                from file_engine.transfer import move_item
                dest_dir = get_location_path(destination)
                res = move_item(resolution["path"], dest_dir)
                if isinstance(res, dict) and res.get("status") == "success":
                    res["message"] = f"Moved {os.path.basename(resolution['path'])} to {destination.title()}."
                return res
            else:
                return resolution

        # COPY
        elif action == "copy":
            destination = action_data.get("destination", "")
            if not destination:
                return "Destination not specified"

            from file_engine.source_resolver import resolve_source
            resolution = resolve_source(target)

            if resolution["status"] == "success":
                from file_engine.transfer import copy_item
                dest_dir = get_location_path(destination)
                res = copy_item(resolution["path"], dest_dir)
                if isinstance(res, dict) and res.get("status") == "success":
                    res["message"] = f"Copied {os.path.basename(resolution['path'])} to {destination.title()}."
                return res
            else:
                return resolution

        return "Unknown action"

    except Exception as e:
        return str(e)
