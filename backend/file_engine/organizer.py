# TODO: Legacy file_engine version can later be removed.
from utils.logger import get_logger
from capabilities.files.organizer.download_organizer import DownloadOrganizer
from capabilities.files.organizer.organization_rules import OrganizationRules
from capabilities.files.organizer.file_classifier import FileClassifier
from utils.constants import CATEGORY_EXTENSIONS
from pathlib import Path

logger = get_logger(__name__)


def get_category_for_file(filename: str) -> str:
    """Determine the category folder for a given file name based on its extension."""

    rules = OrganizationRules(
        category_folders={cat: cat for cat in CATEGORY_EXTENSIONS.keys()},
        extension_map=CATEGORY_EXTENSIONS
    )
    classifier = FileClassifier(rules=rules)
    return classifier.classify(Path(filename))


def organize_directory(path: str) -> dict:
    """Scan all files in the directory and move them to categorized folders.
    Delegates to the modern capabilities DownloadOrganizer.
    """

    summary = {
        "moved_files": 0,
        "categories_created": 0
    }

    if not isinstance(path, str) or not Path(path).exists() or not Path(path).is_dir():
        logger.warning("Invalid directory path for organization: %s", path)
        return summary

    # Configure custom organization rules using legacy mappings for backwards compatibility
    legacy_folders = {cat: cat for cat in CATEGORY_EXTENSIONS.keys()}
    legacy_folders["Others"] = "Others"

    # Check which folders exist BEFORE organizing
    pre_existing_categories = {
        cat for cat in legacy_folders.values()
        if (Path(path) / cat).is_dir()
    }

    rules = OrganizationRules(
        category_folders=legacy_folders,
        extension_map=CATEGORY_EXTENSIONS
    )

    organizer = DownloadOrganizer(rules=rules)
    res = organizer.organize(path)

    if res.get("status") == "success":
        moved_count = res["data"]["moved_count"]
        
        # Check which folders exist AFTER organizing
        post_existing_categories = {
            cat for cat in legacy_folders.values()
            if (Path(path) / cat).is_dir()
        }

        # Categories created: those that exist now but did not exist before
        categories_created = len(post_existing_categories - pre_existing_categories)

        summary["moved_files"] = moved_count
        summary["categories_created"] = categories_created

    logger.info("Legacy organize directory summary wrapper for '%s': %s", path, summary)
    return summary
