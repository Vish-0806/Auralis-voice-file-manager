# TODO: Legacy file_engine version can later be removed.
from typing import Dict, Any
from utils.logger import get_logger
from capabilities.files.source_resolver import SourceResolver
from file_engine.search_engine import search_files

logger = get_logger(__name__)


def resolve_source(target: str) -> Dict[str, Any]:
    """
    Resolves the target file or folder name to a unique path.
    Delegates to the modern capabilities SourceResolver.

    Returns a dictionary with:
    - 'status': 'success', 'disambiguation', or 'error'
    - 'path': Resolved absolute path if status is 'success'
    - 'results': List of matches if status is 'disambiguation'
    - 'message': Description of the result
    """

    logger.info("Resolving source target: '%s' delegating to capabilities.", target)
    resolver = SourceResolver(search_fn=search_files)
    return resolver.resolve(target)
