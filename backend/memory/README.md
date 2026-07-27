# Foundational Memory Subsystem

The Memory Subsystem serves as the foundation for storing, retrieving, ranking, and assembling Auralis agent memories into structured assistant context. It follows Clean Architecture, domain-driven design, and SOLID principles.

## Architecture

The system is organized into decoupled, layered components:

```mermaid
graph TD
    Client[AI Brain / Clients] -->|uses| Service[MemoryService]
    
    subgraph Management [Service & Manager Layer]
        Service -->|delegates to| Manager[MemoryManager]
        Manager -->|aggregates via| ContextBuilder[ContextBuilder]
        ContextBuilder -->|scores via| MemoryRanker[MemoryRanker]
        Manager -->|uses abstract| BaseRepo[BaseRepository]
    end

    subgraph Repository [Data Access Layer]
        BaseRepo <|-- RepoImpl[MemoryRepository]
        RepoImpl -->|uses| BaseProvider[BaseProvider]
        
        RepoImpl -->|specialized repositories| ConvRepo[ConversationRepository]
        RepoImpl -->|specialized repositories| ExecRepo[ExecutionRepository]
        RepoImpl -->|specialized repositories| CtxRepo[ContextRepository]
        RepoImpl -->|specialized repositories| PrefRepo[PreferenceRepository]
    end

    subgraph Storage [Providers Layer]
        BaseProvider <|-- InMemory[InMemoryProvider]
        BaseProvider <|-- PostgreSQL[PostgresProvider]
        
        Factory[ProviderFactory] -->|creates configured| BaseProvider
        Registry[MemoryRegistry] -->|registers & resolves| BaseProvider
    end
```

- **Domain Models (`models/domain_models.py`):** Independent data structures representing core memory units (`MemoryEntry`, `MemoryType`, `MemoryQuery`, `MemoryResult`, `MemoryMetadata`, `AssistantContext`), completely decoupled from database tables or ORM frameworks.
- **Centralized Configuration (`config.py`):** Configures variables like active provider type, database connection URLs, embedding dimensions, cache TTLs, and similarity boundaries, with safe fallback defaults.
- **Service Layer (`manager/memory_service.py`):** The *sole public interface* exposed to the AI Brain. Offers high-level async APIs (`save`, `get`, `search`, `update`, `delete`, `list`, `get_recent_conversations`, `get_conversations_by_session`, `get_recent_executions`, `get_latest_context`, `get_user_preferences`).
- **Context Builder (`manager/context_builder.py`):** Aggregates recent conversations, executions, workspace state, preferences, and workspace profiles into an `AssistantContext` domain model.
- **Memory Ranker (`manager/memory_ranker.py`):** Scores retrieved memories using exponential recency decay, session affinity, workspace path matches, entity token overlap, and command verb similarity.
- **Context Window Config (`manager/context_builder.py`):** Restricts database query limits via `ContextWindowConfig` (`short_term_limit`, `long_term_limit`, `session_limit`) and provides high-performance `session_only` context loading.
- **Repository Pattern (`repository/`):** Decouples business logic from specific persistence clients using SQLAlchemy ORM repositories (`ConversationRepository`, `ExecutionRepository`, `ContextRepository`, `PreferenceRepository`, `MemoryEventRepository`, `RoutineDefinitionRepository`, `ProactiveRecommendationRepository`).
- **Autonomous Routines (`routines/`):** Automatically discovers repeated user behavior, converts repeated execution patterns into reusable routines, safely recommends routine creation, executes approved routines, and monitors performance over time.
- **Proactive Assistant (`proactive/`):** Analyzes historical activity, workspace state, and user feedback to predict user needs and recommend automation suggestions before commands are issued using deterministic scoring.
- **Adaptive Recommendations (`recommendations/`):** Evaluates runtime context and environmental triggers (`WorkspaceOpened`, `ApplicationOpened`, etc.) against confidence thresholds and cooldown policies to suggest workflows.
- **Workflow Mining & Observation (`workflows/`):** Observes real-time execution steps, mines n-gram action patterns, and validates workflow candidates for routine promotion.
- **Workspace Intelligence (`workspace/`):** Asynchronously discovers, scans, and caches workspace folder statistics, Git branch states, and dominant project languages/build tools.
- **Provider Pattern (`providers/`):** Adapts specific database/cache clients to the memory subsystem.
  - `BaseProvider`: Abstract contract defining standard persistence layer APIs.
  - `InMemoryProvider`: Transient, thread-safe in-memory store for local testing and bootstrapping.
  - `PostgresProvider`: Fully active, production-grade PostgreSQL provider supporting session scopes, transactional CRUD, advanced retrieval queries, and vector similarity search.
  - `MemoryRegistry`: Catalog for provider registration and dynamic discovery.
  - `ProviderFactory`: Instantiates and returns the configured provider.

## Usage

```python
import uuid
from memory import (
    MemoryService,
    MemoryEntry,
    MemoryType,
    MemoryQuery,
    ContextBuilder,
    ContextWindowConfig,
    MemoryRankerConfig,
)

# 1. Initialize MemoryService (auto-resolves configured provider, e.g., postgres or in_memory)
memory_service = MemoryService()

# 2. Save a new memory
entry = MemoryEntry(
    id=str(uuid.uuid4()),
    content="User preference: set default terminal to powershell.",
    memory_type=MemoryType.PREFERENCE
)
await memory_service.save(entry)

# 3. Construct ranked AssistantContext for user request
window_cfg = ContextWindowConfig(short_term_limit=5, long_term_limit=10, session_limit=5)
ranker_cfg = MemoryRankerConfig(recency_weight=0.2, session_weight=0.3)
builder = ContextBuilder(memory_service, ranker_config=ranker_cfg, window_config=window_cfg)

assistant_context = await builder.build_context(
    user_id=1,
    session_id="sess_123",
    query_text="open terminal window"
)

print(f"Loaded {len(assistant_context.recent_conversations)} ranked conversations.")
```
