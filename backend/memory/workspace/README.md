# Workspace Profiles Subsystem

The Workspace Profiles subsystem provides a modular, validated, snapshot-capable, and transaction-safe API for reading, writing, duplicating, and launching user desktop setups in Auralis.

## Features

- **Built-in Templates:** Provide default setups for `Coding`, `Study`, `Meeting`, `Gaming`, and `Presentation` templates.
- **Desktop Automation:** Launches workspace application structures safely using `DesktopCapability`.
- **Workspace Snapshots:** Utility to capture active paths and windows to instantly save custom profile setups.

## Usage

```python
from memory import WorkspaceService

# Instantiate service (resolves database connection and Desktop Capability automatically)
ws_service = WorkspaceService()

# 1. Create a workspace profile using a built-in template configuration
coding_tmpl = ws_service.get_template("coding")
ws_service.create(user_id=1, name="my_code_profile", path=coding_tmpl["path"], settings=coding_tmpl["settings"])

# 2. List user profiles
profiles = ws_service.list(user_id=1)

# 3. Restore and launch a workspace profile (routes executions to DesktopCapability)
profile = ws_service.get_by_name(user_id=1, name="my_code_profile")
ws_service.restore(user_id=1, profile_id=profile.id)

# 4. Capture current desktop state and save it as a new profile snapshot
from memory import ContextService
ctx_service = ContextService()
ws_service.snapshot(user_id=1, session_id="sess_123", profile_name="captured_workspace", context_service=ctx_service)
```
