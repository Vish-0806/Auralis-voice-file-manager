# File Engine Migration Report

This report summarizes the comparison and migration of legacy file logic from `backend/file_engine` to the clean capabilities-based architecture in `backend/capabilities/files`.

## Files Compared

| Legacy File (`backend/file_engine/`) | New Capability File (`backend/capabilities/files/`) | Status / Action |
| :--- | :--- | :--- |
| `path_resolver.py` | `path_resolver.py` | Migrated and delegated |
| `search_engine.py` | `search_engine.py` | Migrated and delegated |
| `source_resolver.py` | `source_resolver.py` (New) | Migrated and delegated |
| `transfer.py` | `transfer_service.py` | Migrated and delegated |
| `organizer.py` | `organizer/download_organizer.py` | Migrated and delegated |
| `permissions.py` | N/A | Retained empty stub with TODO |
| `file_operations.py` | `file_capability.py` / Services | Retained legacy wrapper with TODO |

## Logic Migrated

1. **Path Resolution**:
   - Added `"music"` and `"videos"` directories to `PathResolver._SUPPORTED_FOLDERS` to match legacy support for multiple system directories.
   - Refactored `PathResolver` to use mock-friendly `os.path.exists` checks to align with legacy unit tests.

2. **File & Directory Transfers**:
   - Extended `TransferService` to support copying/moving directories using `shutil.copytree`.
   - Added automatic creation of destination folders if they do not exist.
   - Integrated unique naming collision resolution (appending suffixes like `_1`, `_2`) during file transfer conflicts.

3. **Source Path Resolution**:
   - Created a new `SourceResolver` capability that encapsulates direct check and search-based path resolution.
   - Supported injection of custom/legacy search functions to preserve mock patches in legacy tests.

4. **Directory Organization**:
   - Created a robust custom configuration for `DownloadOrganizer` that uses the legacy `CATEGORY_EXTENSIONS` mapping.
   - Re-implemented the directories created counter check on pre-existing versus post-existing folders.

## Imports & Wrapping Strategy

To guarantee the project still runs exactly as before, the legacy modules in `backend/file_engine` were re-implemented as wrapper interfaces that instantiate the corresponding capability service under the hood:
- `file_engine.search_engine.search_files` delegates to `SearchEngine`
- `file_engine.source_resolver.resolve_source` delegates to `SourceResolver`
- `file_engine.transfer.copy_item` / `move_item` delegates to `TransferService`
- `file_engine.organizer.organize_directory` delegates to `DownloadOrganizer`

All legacy files have been marked with a `TODO` comment indicating that the legacy version can later be removed.

## Remaining Work

1. **Voice and App Integration**:
   - Transition the REST routes and voice listeners (e.g. `voice/listener.py`, `voice/voice_session.py`, `api/file_routes.py`) to call the new `FileCapability` dispatcher actions directly rather than using legacy `file_operations.py`.
2. **Deprecate Legacy Directory**:
   - Once all direct callers and unit tests have been updated to target the `capabilities/files` folder, `backend/file_engine` can be completely deleted.
