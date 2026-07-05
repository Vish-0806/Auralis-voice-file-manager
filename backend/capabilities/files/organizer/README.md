# Intelligent Downloads Organizer

This package implements the Downloads Organizer capability for Auralis. It automatically scans, classifies, and organizes files in the Downloads directory into target categories.

## Architecture

The organizer is structured using modular components:

1. **OrganizationRules**: Manages configurable mappings between file extensions, categories, and target folder names.
2. **FileClassifier**: Analyzes a file to determine its category. Designed to support rule-based lookups and future semantic/AI-based classifications.
3. **ReportGenerator**: Collects metrics and aggregates run summaries (scanned, moved, skipped, errors) in human-readable and structured JSON shapes.
4. **DownloadOrganizer**: Coordinates scanning the directory, invoking the classifier, applying safety rules, moving files, and invoking the report builder.

## Safety Guarantees

- **Overwrite Prevention**: Files are never overwritten. When destination path collisions occur, a unique sequence number is automatically appended to the filename.
- **System and Hidden Files Filtering**: System files (e.g. `desktop.ini`, `thumbs.db`) and hidden files (starting with `.`) are ignored automatically.
- **Directory Reuse**: Standard directories are created and reused gracefully.
