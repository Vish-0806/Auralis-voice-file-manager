# FileCapability

## Purpose

`FileCapability` is the first file-focused execution capability in Auralis. It provides the foundation for file and folder intents without performing any operating system interaction yet.

## Responsibilities

- Accept a file-related execution request from the dispatcher.
- Validate the request as an `ExecutionPlan`.
- Support the `OPEN_FOLDER` intent only.
- Return a structured `ExecutionResult` for the core layer.

## Execution Flow

1. The dispatcher sends the action and arguments into `FileCapability`.
2. The capability normalizes the request into an `ExecutionPlan`.
3. The plan is validated to ensure the intent is supported.
4. The capability returns a non-destructive result with the message `FileCapability received OPEN_FOLDER request for <target>`.
5. The dispatcher wraps the payload into its normal orchestration result path.

## Future Expansion

This package is intentionally narrow for Phase 2 Step 2.1. Future steps can add:

- Folder opening through a real OS adapter.
- File search and listing.
- Copy, move, rename, and delete flows.
- Safe folder creation.
- Organizer workflows and deeper file automation.# Files Capability
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
