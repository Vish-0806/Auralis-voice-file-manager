# Memory Subsystem ORM Models

Provides the declarative database schemas for the Auralis memory sub-layer modules, built using SQLAlchemy 2.x and Pydantic.

## Models Schema & Relationships

The database mapping comprises a core `User` model, serving as the root parent, and 7 dependent models representing different tiers of Auralis's local memory store:

```mermaid
erDiagram
    users ||--o{ preferences : owns
    users ||--o{ workspace_profiles : owns
    users ||--o{ contexts : owns
    users ||--o{ conversation_history : owns
    users ||--o{ routine_learning : owns
    users ||--o{ execution_history : owns
    users ||--o{ memory_events : owns

    users {
        int id PK
        string username UK
        string email UK
        datetime created_at
        datetime updated_at
    }
    preferences {
        int id PK
        int user_id FK
        string key
        jsonb value
        datetime created_at
        datetime updated_at
    }
    workspace_profiles {
        int id PK
        int user_id FK
        string name
        string path
        jsonb settings
        datetime created_at
        datetime updated_at
    }
    contexts {
        int id PK
        int user_id FK
        string session_id
        string active_window
        string workspace_path
        jsonb metadata_bag
        datetime created_at
        datetime updated_at
    }
    conversation_history {
        int id PK
        int user_id FK
        string session_id
        string role
        string content
        int token_count
        datetime created_at
    }
    routine_learning {
        int id PK
        int user_id FK
        string trigger_event
        jsonb action_sequence
        float confidence_score
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    execution_history {
        int id PK
        int user_id FK
        string action
        string status
        int duration_ms
        string logs
        jsonb input_parameters
        jsonb output_result
        datetime created_at
    }
    memory_events {
        int id PK
        int user_id FK
        string event_type
        jsonb payload
        datetime created_at
    }
```

* **Cascades:** All foreign keys pointing to `users.id` configure `ondelete="CASCADE"`, meaning when a User is deleted, all their associated database records are automatically deleted.
* **JSONB Fields:** Used to hold complex settings parameters, trigger action histories, execution bags, and dynamically published payloads, which allows standard key/index search optimizations in PostgreSQL.

## Metadata Auto-Discovery

To make sure Alembic (the database migration framework) can automatically generate database upgrade scripts, the package initialization file `__init__.py` imports all models. This hooks them onto the shared `Base.metadata` registry. When configuring Alembic, reference this metadata:

```python
from memory.database import Base
target_metadata = Base.metadata
```
