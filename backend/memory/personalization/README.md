# Personalization Engine

The Personalization Engine consolidates all available memory sources (Preferences, Context Memory, Workspace Profiles, Routine Learning) into a single User Profile, evaluates personalized execution contexts, and produces recommended actions list suggestions based on behavior signals.

## Features

- **Consolidated User Profile:** Aggregates active workspace paths, theme settings, active routines counts, and recently run actions.
- **Deterministic Conflict Resolution:** Resolves config variables by checking priority sources in exact order:
  1. Explicit User Command (Request Overrides)
  2. Current Context
  3. Workspace Profile settings
  4. User Preferences
  5. Learned Routine
  6. System Defaults
- **Personalized Suggestions:** Recommends workspace loads, theme switches, or routine runs based on active paths or temporal cues.

## Usage

```python
from memory import PersonalizationService

# Instantiate service (resolves all memory service modules automatically)
personalization = PersonalizationService()

# 1. Generate consolidated user profile summary
profile = personalization.profile(user_id=1, session_id="sess_123")
print(f"Active workspace path: {profile.active_workspace_path}")
print(f"Routines count: {profile.active_routines_count}")

# 2. Get personalized context (deterministic priority settings resolution)
overrides = {"theme": "light"}  # Force light theme for this specific command run
personalized = personalization.context(user_id=1, session_id="sess_123", user_overrides=overrides)

print(f"Resolved theme: {personalized.resolved_settings['theme']}")  # 'light' (Explicit Override)
print(f"Resolved editor: {personalized.resolved_settings['editor']}")  # e.g., 'VS Code' (Preference / Default)
print(f"Theme source: {personalized.source_mapping['theme']}")  # 'Explicit User Command'

# 3. Pull contextual suggestions
suggestions = personalization.recommendations(user_id=1, session_id="sess_123")
for sugg in suggestions:
    print(f"Type: {sugg.type}")
    print(f"Message: {sugg.message}")
```
