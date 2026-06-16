import os
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

def search_files(query: str) -> List[Dict[str, str]]:
    """
    Search recursively for files matching the query in Desktop, Documents, and Downloads.
    
    Args:
        query: The search term (file name or part of it).
        
    Returns:
        A list of dicts with keys 'name', 'path', and 'type'.
    """
    if not isinstance(query, str) or not query.strip():
        logger.info("Empty query received. Returning empty list.")
        return []

    query_lower = query.lower().strip()
    home_dir = os.path.expanduser("~")
    
    # Define directories to search
    search_dirs = [
        os.path.join(home_dir, "Desktop"),
        os.path.join(home_dir, "Documents"),
        os.path.join(home_dir, "Downloads")
    ]
    
    results = []
    
    logger.info(f"Starting file search for query: '{query}' in Desktop, Documents, and Downloads.")
    
    def handle_walk_error(err: OSError):
        # Gracefully log permission errors and other OS errors
        logger.warning(f"Error accessing directory '{err.filename}': {err}")

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            logger.info(f"Search directory does not exist, skipping: {search_dir}")
            continue
            
        logger.info(f"Searching in directory: {search_dir}")
        
        try:
            for root, dirs, files in os.walk(search_dir, topdown=True, onerror=handle_walk_error):
                for file in files:
                    if query_lower in file.lower():
                        abs_path = os.path.join(root, file)
                        _, ext = os.path.splitext(file)
                        
                        results.append({
                            "name": file,
                            "path": abs_path,
                            "type": ext
                        })
                        
                        if len(results) >= 20:
                            logger.info(f"Match limit reached (20). Stopping search.")
                            return results
        except Exception as e:
            logger.error(f"Unexpected error walking directory {search_dir}: {e}")
                        
    logger.info(f"File search completed. Found {len(results)} matches.")
    return results
