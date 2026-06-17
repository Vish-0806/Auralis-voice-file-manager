"""
Auralis System Constants
"""

# Reusable file extension mappings by category
CATEGORY_EXTENSIONS = {
    "PDFs": {".pdf"},
    "Images": {
        ".png", ".jpg", ".jpeg", ".gif", ".webp",
        ".bmp", ".tiff", ".svg", ".heic", ".heif", ".ico"
    },
    "Videos": {
        ".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv",
        ".m4v", ".webm", ".3gp"
    },
    "Documents": {
        ".docx", ".doc", ".txt", ".pptx", ".xlsx",
        ".rtf", ".odt", ".xls", ".ppt", ".csv",
        ".pages", ".key", ".numbers", ".epub", ".ods", ".odp"
    },
    "Archives": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz",
        ".bz2", ".xz"
    },
    "Code": {
        ".py", ".java", ".js", ".cpp", ".c", ".html", ".css",
        ".ts", ".sh", ".bat", ".json", ".xml", ".yaml", ".yml",
        ".md", ".go", ".rs", ".cs", ".sql", ".h", ".php"
    },
}
