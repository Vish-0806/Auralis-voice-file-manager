"""
Auralis File Engine Package
Contains file operations and path resolution logic.
"""

from file_engine.search_engine import search_files
from file_engine.organizer import organize_directory
from file_engine.transfer import copy_item, move_item
from file_engine.source_resolver import resolve_source

__all__ = ["search_files", "organize_directory", "copy_item", "move_item", "resolve_source"]
