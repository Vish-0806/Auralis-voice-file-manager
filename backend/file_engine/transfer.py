import os
import shutil
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_unique_destination(source: str, destination: str) -> str:
    """
    Determine a unique destination path within the destination folder to avoid collisions.
    Appends a counter suffix (e.g. _1, _2) before the extension for files, or at the end
    of the directory name for folders.
    """
    basename = os.path.basename(source)
    if os.path.isfile(source):
        name, ext = os.path.splitext(basename)
    else:
        name, ext = basename, ""

    dest_path = os.path.join(destination, basename)
    counter = 1
    while os.path.exists(dest_path):
        if ext:
            new_name = f"{name}_{counter}{ext}"
        else:
            new_name = f"{name}_{counter}"
        dest_path = os.path.join(destination, new_name)
        counter += 1
    return dest_path


def copy_item(source: str, destination: str) -> dict:
    """
    Copy a file or directory to a destination folder.
    Creates destination folders if they do not exist.
    Handles duplicate names safely by renaming.
    Returns a structured success/error dict.
    """
    if not source or not destination:
        return {
            "status": "error",
            "message": "Source and destination must be non-empty paths.",
            "error_class": "ValueError",
        }

    if not os.path.exists(source):
        logger.error("Copy failed: Source path '%s' does not exist.", source)
        return {
            "status": "error",
            "message": f"Source path '{source}' does not exist.",
            "error_class": "FileNotFoundError",
        }

    try:
        # Create destination directory if it does not exist
        os.makedirs(destination, exist_ok=True)

        dest_path = _get_unique_destination(source, destination)
        logger.info("Copying '%s' to '%s'", source, dest_path)

        if os.path.isdir(source):
            shutil.copytree(source, dest_path)
        else:
            shutil.copy2(source, dest_path)

        logger.info("Successfully copied '%s' to '%s'", source, dest_path)
        return {
            "status": "success",
            "message": f"Successfully copied '{os.path.basename(source)}' to '{os.path.basename(dest_path)}'.",
            "source": source,
            "destination": dest_path,
        }

    except PermissionError as pe:
        logger.error("Permission error copying '%s' to '%s': %s", source, destination, pe)
        return {
            "status": "error",
            "message": f"Permission denied while copying '{os.path.basename(source)}'.",
            "error_class": "PermissionError",
            "error": str(pe),
        }
    except Exception as exc:
        logger.error("Error copying '%s' to '%s': %s", source, destination, exc)
        return {
            "status": "error",
            "message": f"An error occurred while copying: {str(exc)}",
            "error_class": exc.__class__.__name__,
            "error": str(exc),
        }


def move_item(source: str, destination: str) -> dict:
    """
    Move a file or directory to a destination folder.
    Creates destination folders if they do not exist.
    Handles duplicate names safely by renaming.
    Returns a structured success/error dict.
    """
    if not source or not destination:
        return {
            "status": "error",
            "message": "Source and destination must be non-empty paths.",
            "error_class": "ValueError",
        }

    if not os.path.exists(source):
        logger.error("Move failed: Source path '%s' does not exist.", source)
        return {
            "status": "error",
            "message": f"Source path '{source}' does not exist.",
            "error_class": "FileNotFoundError",
        }

    try:
        # Create destination directory if it does not exist
        os.makedirs(destination, exist_ok=True)

        dest_path = _get_unique_destination(source, destination)
        logger.info("Moving '%s' to '%s'", source, dest_path)

        shutil.move(source, dest_path)

        logger.info("Successfully moved '%s' to '%s'", source, dest_path)
        return {
            "status": "success",
            "message": f"Successfully moved '{os.path.basename(source)}' to '{os.path.basename(dest_path)}'.",
            "source": source,
            "destination": dest_path,
        }

    except PermissionError as pe:
        logger.error("Permission error moving '%s' to '%s': %s", source, destination, pe)
        return {
            "status": "error",
            "message": f"Permission denied while moving '{os.path.basename(source)}'.",
            "error_class": "PermissionError",
            "error": str(pe),
        }
    except Exception as exc:
        logger.error("Error moving '%s' to '%s': %s", source, destination, exc)
        return {
            "status": "error",
            "message": f"An error occurred while moving: {str(exc)}",
            "error_class": exc.__class__.__name__,
            "error": str(exc),
        }
