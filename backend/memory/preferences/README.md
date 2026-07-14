# User Preference Engine

The Preference subsystem provides a modular, validated, cached, and transaction-safe API for reading and writing user configurations in Auralis.

## Features

- **Schema Validation:** Verifies that settings belong to valid categories/keys and conform to expected data types.
- **TTL Cache:** An in-memory, thread-safe cache invalidates itself on updates and prevents database round-trips for frequently read keys.
- **Fallbacks:** Automatically falls back to schema defaults when querying uninitialized preferences.

## Usage

```python
from memory import PreferenceService

# Instantiate service (resolves database connection automatically)
pref_service = PreferenceService()

# 1. Create a preference
pref_service.create(user_id=1, category="ide", key="theme", value="synthwave")

# 2. Retrieve a preference (hits cache if populated, else DB, else defaults)
theme = pref_service.get(user_id=1, category="ide", key="theme")

# 3. Update a preference
pref_service.update(user_id=1, category="ide", key="theme", value="vs-dark")

# 4. List all preferences (merged with defaults)
all_prefs = pref_service.list(user_id=1)

# 5. Reset preferences back to defaults
pref_service.reset(user_id=1, category="ide")
```
