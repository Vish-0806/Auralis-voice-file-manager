import os
import shutil

HOME_DIR = os.path.expanduser("~")

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


def execute_action(action_data):

    action = action_data["action"]
    target = action_data["target"]

    path = get_target_path(target)

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

        return "Unknown action"

    except Exception as e:
        return str(e)