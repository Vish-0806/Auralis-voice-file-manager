# Foundational Memory Subsystem

The Memory Subsystem serves as the foundation for storing, retrieving, and searching Auralis agent memories. It follows Clean Architecture, domain-driven design, and SOLID principles.

## Architecture

The system is organized into decoupled layers:

```mermaid
graph TD
    Client[AI Brain / Clients] -->|uses| Service[MemoryService]
    
    subgraph Management [Service & Manager Layer]
        Service -->|delegates to| Manager[MemoryManager]
        Manager -->|uses abstract| BaseRepo[BaseRepository]
    end

    subgraph Repository [Data Access Layer]
        BaseRepo <|-- RepoImpl[MemoryRepository]
        RepoImpl -->|uses| BaseProvider[BaseProvider]
    end

    subgraph Storage [Providers Layer]
        BaseProvider <|-- InMemory[InMemoryProvider]
        BaseProvider <|.. PostgreSQL[Future PostgreSQL Provider]
        
        Factory[ProviderFactory] -->|creates configured| BaseProvider
        Registry[MemoryRegistry] -->|registers & resolves| BaseProvider
    end
```

- **Domain Models (`models/domain_models.py`):** Independent data structures representing core memory units (`MemoryEntry`, `MemoryType`, `MemoryQuery`, `MemoryResult`, `MemoryMetadata`), completely decoupled from database tables or ORM frameworks.
- **Centralized Configuration (`config.py`):** Configures variables like active provider type, embedding dimensions, cache TTLs, and similarity boundaries, with safe fallback defaults.
- **Service Layer (`manager/memory_service.py`):** The *sole public interface* exposed to the AI Brain. Offers high-level async APIs (`save`, `get`, `search`, `update`, `delete`, `list`).
- **Manager Layer (`manager/memory_manager.py`):** Orchestrates memory domain business logic, coordinating between repositories and formatting inputs/outputs into domain models.
- **Repository Pattern (`repository/`):** Decouples business logic from specific persistence clients.
  - `BaseRepository`: Abstract contract defining database-neutral operations.
  - `MemoryRepository`: Concrete repository implementation delegating work to a resolved storage provider.
- **Provider Pattern (`providers/`):** Adapts specific database/cache clients to the memory subsystem.
  - `BaseProvider`: Abstract contract defining standard persistence layer APIs.
  - `InMemoryProvider`: A default, transient, thread-safe in-memory store for local testing and bootstrapping.
  - `MemoryRegistry`: Catalog for provider registration and dynamic discovery.
  - `ProviderFactory`: Instantiates and returns the configured provider.

## Usage

```python
import uuid
from backend.memory import MemoryService, MemoryEntry, MemoryType, MemoryQuery

# Initialize service (auto-resolves default transient provider)
memory_service = MemoryService()

# 1. Save a new memory
entry = MemoryEntry(
    id=str(uuid.uuid4()),
    content="User preference: set default terminal to powershell.",
    memory_type=MemoryType.PREFERENCE
)
await memory_service.save(entry)

# 2. Search memories
query = MemoryQuery(
    text="terminal",
    memory_type=MemoryType.PREFERENCE
)
results = await memory_service.search(query)
for result in results:
    print(f"Memory: {result.entry.content} (Score: {result.score})")
```
