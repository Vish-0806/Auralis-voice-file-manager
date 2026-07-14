# Memory Coordinator Platform

The Memory Coordinator serves as the single unified entry point for all tiered memory system operations in Auralis. Subsystems (such as the AI Brain) query or update user settings, active context, workspaces, learned routines, and personalization parameters exclusively through this coordinator.

## Features

- **Encapsulated Memory Services:** Hides raw repository schemas and dependencies from business modules.
- **Personalization Pipeline:** Integrates preferences, temporal cues, directories, and routines, conflict-resolving settings sequentially using priority mapping rules.
- **Platform Health Diagnostics:** Probes database connection states, validates context cache lookups, and outputs registry metrics (such as active sessions count and routines count).
- **Service Registry:** Allows registering third-party memory plugin services dynamically.

## Usage

```python
from memory import MemoryCoordinator

# Instantiate coordinator
coordinator = MemoryCoordinator()

# 1. Access Preferences
coordinator.set_preference(user_id=1, category="ide", setting_key="theme", value="dark")

# 2. Access Context
coordinator.save_context(user_id=1, session_id="sess_123", context_type="current_project", value="/home/projects")

# 3. Restore Workspace
coordinator.restore_workspace(user_id=1, profile_id=12)

# 4. Trigger Context Personalization Pipeline
personalized = coordinator.run_pipeline(user_id=1, session_id="sess_123")
print(personalized.resolved_settings["theme"])  # e.g., 'dark'

# 5. Check Coordinator Platform Health status
health = coordinator.check_health()
print(f"Database health: {health['database']}")  # 'healthy'
```
