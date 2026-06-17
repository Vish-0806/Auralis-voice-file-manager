import os
import shutil
from .search_engine import search_files

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

            if os.path.exists(path):

                if os.path.isfile(path):
                    os.remove(path)

                elif os.path.isdir(path):
                    shutil.rmtree(path)

                return f"{target} deleted"

            return f"{target} not found"

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
            from .organizer import organize_directory
            summary = organize_directory(path)
            return f"Successfully organized {target.title()} folder. Moved {summary['moved_files']} files into {summary['categories_created']} categories."

        # MOVE
        elif action == "move":
            destination = action_data.get("destination", "")
            if not destination:
                return "Destination not specified"

            from .source_resolver import resolve_source
            resolution = resolve_source(target)

            if resolution["status"] == "success":
                from .transfer import move_item
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

            from .source_resolver import resolve_source
            resolution = resolve_source(target)

            if resolution["status"] == "success":
                from .transfer import copy_item
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