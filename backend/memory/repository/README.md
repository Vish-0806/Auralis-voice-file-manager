# Memory Subsystem Repository Layer

Provides decoupled database access adapters (using the Repository Pattern) mapping the business domain representation to database ORM structures.

## Repositories Hierarchy & Usage

All repositories inherit generic CRUD methods from `BaseRepository`:

* **`UserRepository`**: Handles user storage and search.
* **`PreferenceRepository`**: Handles configuration key-values.
* **`WorkspaceRepository`**: Handles user active workspace paths.
* **`ContextRepository`**: Handles focused application context states.
* **`ConversationRepository`**: Handles conversation turns.
* **`RoutineRepository`**: Handles learned trigger routines.
* **`ExecutionRepository`**: Handles audit log triggers.
* **`MemoryEventRepository`**: Handles published state updates.

## RepositoryFactory

To facilitate dependency injection and manage connection lifecycles, repositories are resolved using `RepositoryFactory`:

```python
from memory.database import SessionLocal
from memory.repository import RepositoryFactory

# 1. Open Session
db = SessionLocal()

# 2. Instantiate Factory
factory = RepositoryFactory(db)

# 3. Retrieve Repository and perform CRUD using Domain Models
user_repo = factory.get_user_repository()

# Create User
from memory.models.domain_models import UserDomain
user_domain = UserDomain(username="jane_doe", email="jane@example.com")
saved_user = user_repo.create(user_domain)

# Find by username
found_user = user_repo.get_by_username("jane_doe")
```

All interactions between the caller and the repository layers accept and return *Domain Models* (defined in `memory.models.domain_models`), completely isolating database schemas and connection sessions.
