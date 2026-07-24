# Workspace Profiles & Intelligence Subsystem

The Workspace Profiles and Workspace Intelligence subsystem provides a modular, validated, snapshot-capable, and transaction-safe API for reading, writing, duplicating, and launching user desktop setups, combined with dynamic file-crawling, metadata-indexing, and language/git/build intelligence detection.

---

## 1. Workspace Profiles (Database & Automation)

* **Built-in Templates:** Provide default setups for `Coding`, `Study`, `Meeting`, `Gaming`, and `Presentation` templates.
* **Desktop Automation:** Launches workspace application structures safely using `DesktopCapability`.
* **Workspace Snapshots:** Utility to capture active paths and windows to instantly save custom profile setups.

### Profile Usage Example
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

---

## 2. Workspace Intelligence (Dynamic Indexing & Analysis)

* **Workspace Discovery:** Scans search roots asynchronously to detect candidate workspaces while skipping ignored folders (`venv`, `node_modules`, `build`, etc.) and duplicate nested project roots.
* **FS Indexer:** Asynchronously indexes folder stats and file details without reading payloads, generating file trees.
* **Project Intelligence:** Detects project boundaries, dominant programming languages, build tools, recommended build commands, and Git branches/porcelain states via lightweight subprocess commands.
* **Caching Coordinator:** Caches the parsed `WorkspaceAnalysis` domain models inside a thread-safe in-memory cache with configurable TTL validation (default 5 minutes).
* **AI Integration:** Passes compiled workspace analysis through `ContextBuilder` directly to the `BrainController` pipeline.

### Intelligence Usage Example
```python
from memory.workspace import WorkspaceIntelligenceCoordinator

# Instantiate coordinator (will resolve indexers and engines automatically)
coordinator = WorkspaceIntelligenceCoordinator(cache_ttl=300.0)

# Run full crawl, project analysis, and Git inspection (utilizes cache if valid)
analysis = await coordinator.analyze("/my/project/path")

print(f"Project Name: {analysis.project_name}")
print(f"Dominant Language: {analysis.dominant_language}")
print(f"Build System: {analysis.build_system}")
print(f"Git Active Branch: {analysis.git_branch}")
print(f"Is Dirty: {analysis.git_dirty}")
print(f"File stats: {analysis.total_files} files, {analysis.total_size} bytes")
```
