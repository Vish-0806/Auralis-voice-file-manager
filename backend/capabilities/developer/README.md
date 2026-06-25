# Developer Assistant Capability
## Purpose
Developer productivity routines, Git workflows, and terminal shells management.

## Architecture
- `git.py`: Git commit, status, and branch operations.
- `terminal.py`: Manages persistent shell execution processes.
- `docker.py`: Evaluates active container runtimes.
- `vscode.py`: Controls VS Code workspaces.
- `python.py` / `node.py` / `java.py`: Checks runtime environments and packages.

## Relationships
- **Core:** The Dispatcher runs shells and commits code.
- **Memory:** Diagnostic traces are cached to help explain errors.
- **Events:** Emits events when builds fail or containers stop.
- **OS Layer:** Spawns subprocess shells via the OSAL Terminal Port.
