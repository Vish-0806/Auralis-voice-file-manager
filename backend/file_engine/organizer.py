import os
import shutil
from utils.logger import get_logger
from utils.constants import CATEGORY_EXTENSIONS

logger = get_logger(__name__)


def get_category_for_file(filename: str) -> str:
    """Determine the category folder for a given file name based on its extension."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category
    return "Others"


def _get_unique_path(dest_dir: str, filename: str) -> str:
    """Resolve naming collisions by appending a counter suffix to the filename."""
    name, ext = os.path.splitext(filename)
    dest_path = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{name}_{counter}{ext}")
        counter += 1
    return dest_path


def organize_directory(path: str) -> dict:
    """Scan all files in the directory and move them to categorized folders.

    Skips subdirectories, resolves duplicate filenames safely, handles permission
    errors gracefully, and returns a summary dict.
    """
    summary = {
        "moved_files": 0,
        "categories_created": 0
    }

    if not isinstance(path, str) or not os.path.exists(path) or not os.path.isdir(path):
        logger.warning("Invalid directory path for organization: %s", path)
        return summary

    try:
        entries = list(os.scandir(path))
    except PermissionError as e:
        logger.error("Permission error scanning directory '%s': %s", path, e)
        return summary
    except Exception as e:
        logger.error("Unexpected error scanning directory '%s': %s", path, e)
        return summary

    created_dirs = set()

    for entry in entries:
        try:
            # Skip directories (this also skips the category folders we create)
            if not entry.is_file(follow_symlinks=False):
                continue

            filename = entry.name
            category = get_category_for_file(filename)
            category_dir = os.path.join(path, category)

            # Create folder automatically if missing
            if not os.path.exists(category_dir):
                try:
                    os.makedirs(category_dir, exist_ok=True)
                    created_dirs.add(category_dir)
                except PermissionError as e:
                    logger.error("Permission error creating directory '%s': %s", category_dir, e)
                    continue
                except Exception as e:
                    logger.error("Error creating directory '%s': %s", category_dir, e)
                    continue
            elif not os.path.isdir(category_dir):
                # A file exists with the same name as the category folder. Skip moving into it.
                logger.warning("Cannot organize file '%s' into '%s' because a file with that name exists", filename, category_dir)
                continue

            src_path = entry.path
            dest_path = _get_unique_path(category_dir, filename)

            # Move file using shutil
            shutil.move(src_path, dest_path)
            summary["moved_files"] += 1

        except PermissionError as e:
            logger.error("Permission error moving file '%s': %s", entry.name, e)
        except Exception as e:
            logger.error("Error processing file '%s': %s", entry.name, e)

    summary["categories_created"] = len(created_dirs)
    logger.info("Organize directory summary for '%s': %s", path, summary)
    return summary
