# TODO: Legacy file_engine version can later be removed.
from utils.logger import get_logger
from capabilities.files.transfer_service import TransferService

logger = get_logger(__name__)


def copy_item(source: str, destination: str) -> dict:
    """
    Copy a file or directory to a destination folder.
    Delegates to TransferService.
    """

    logger.info("Legacy copy_item delegation to TransferService: '%s' -> '%s'", source, destination)
    service = TransferService()
    return service.copy_file(source, destination)


def move_item(source: str, destination: str) -> dict:
    """
    Move a file or directory to a destination folder.
    Delegates to TransferService.
    """

    logger.info("Legacy move_item delegation to TransferService: '%s' -> '%s'", source, destination)
    service = TransferService()
    return service.move_file(source, destination)
