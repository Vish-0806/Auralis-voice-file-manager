# Files Capability
## Purpose
Intelligent file system navigation, recursive searches, and directory organization.

## Architecture
- `operations.py`: Basic CRUD actions (create, delete, copy, rename).
- `organization.py`: Decoupled directory auto-sorting rules.
- `search.py`: Recursive search engine queries.
- `indexing.py`: File search index updating hooks.

## Relationships
- **Core:** The Dispatcher calls operations using path parameters.
- **Memory:** Search queries are cached to improve retrieval speeds.
- **Events:** Publishes `capability.file_created` and `capability.file_deleted` events.
- **OS Layer:** Interfaces with the File System Port to execute actions.
