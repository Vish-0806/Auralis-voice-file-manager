"""
Auralis File Engine Package
Contains file operations and path resolution logic.
"""

from .search_engine import search_files
from .organizer import organize_directory

__all__ = ["search_files", "organize_directory"]
