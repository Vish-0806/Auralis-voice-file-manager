# Context Memory

The Context Memory subsystem provides a modular, validated, cached, and transaction-safe API for reading, writing, and restoring active execution context states in Auralis.

## Features

- **Schema Validation:** Verifies that context types conform to allowed values (such as project, terminal, or clipboard contexts) and shapes.
- **TTL Cache:** An in-memory, thread-safe cache invalidates itself on updates and prevents database round-trips for frequently read states.
- **Context Expiration:** Policies to expire temporary contexts automatically.

## Usage

```python
from memory import ContextService

# Instantiate service (resolves database connection automatically)
ctx_service = ContextService()

# 1. Save context (e.g. current project path)
ctx_service.save(user_id=1, session_id="sess_123", context_type="current_project", value="/home/user/project")

# 2. Save temporary context with a short TTL (10 seconds)
ctx_service.save(user_id=1, session_id="sess_123", context_type="temporary", value="temporary_task_data", ttl_seconds=10)

# 3. Load active context values (filters out expired items automatically)
active_ctx = ctx_service.load(user_id=1, session_id="sess_123")

# 4. Delete context entry
ctx_service.delete(user_id=1, session_id="sess_123", context_type="current_project")

# 5. Restore full context bag
ctx_service.restore(user_id=1, session_id="sess_123", metadata_bag={"clipboard": "restored text"})
```
