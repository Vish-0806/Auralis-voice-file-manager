# Dependency Graph

This document analyzes the current import topology of the Auralis backend, identifies coupling risks, and provides a target dependency flow for the redesigned architecture.

---

## Analysis of the Current Codebase

1. **High Coupling / Command Dependency:**
   In the legacy structure, API routes (`api/routes.py`) and controllers (`app/controller.py`) import concrete executors directly (e.g. `from file_engine.file_operations import execute_action`). This prevents testing the routes without running active disk IO modifications.
2. **Circular Import Risks:**
   During the previous refactoring of `file_routes.py` and `search_engine.py` imports, circular paths were resolved by moving helpers to `utils/`. In the future planner-based architecture, circular dependencies are prevented by requiring all subsystems (AI, Memory, OSAL) to reference only interface ports (`interfaces.py`) rather than concrete classes.
3. **Low Cohesion:**
   Legacy modules like `file_engine/path_resolver.py` and `file_engine/permissions.py` are platform-specific (tied to Windows directory parameters) but reside within the general file operations directory. These must be moved to platform adapters under the OS Abstraction Layer (OSAL).

---

## Legacy Dependency Graph

The legacy application is highly coupled, with the entry points importing concrete engines directly:

```mermaid
graph TD
    main_py[main.py] --> routes[api/routes.py]
    main_py --> voice_routes[api/voice_routes.py]
    
    routes --> command_parser[ai_engine/command_parser.py]
    routes --> file_ops[file_engine/file_operations.py]
    
    voice_routes --> listen[voice_engine/speech_to_text.py]
    voice_routes --> command_parser
    voice_routes --> file_ops
    
    file_ops --> path_resolver[file_engine/path_resolver.py]
    file_ops --> permissions[file_engine/permissions.py]
    file_ops --> search[file_engine/search_engine.py]
```

---

## Target Redesigned Dependency Graph

The redesigned architecture uses interfaces to decouple components. Low-level adapters and capabilities implement abstract interfaces and are injected into the Core Assistant:

```mermaid
graph TD
    %% Core Orchestrator
    subgraph CoreModule [Core Subsystem]
        Assistant[core/assistant.py]
        Planner[core/planner.py]
        Dispatcher[core/dispatcher.py]
    end

    %% Port Interfaces
    subgraph InterfacesModule [Abstract Ports & Interfaces]
        IAgentBrain[core/interfaces.py]
        IMemoryManager[memory/interfaces.py]
        IEventBus[events/interfaces.py]
        IOSAdapter[core/interfaces.py]
        ICapability[core/interfaces.py]
    end

    %% Implementations
    subgraph Impls [Concrete Implementations]
        Agent[ai/agent.py]
        Memory[memory/manager.py]
        EventBus[events/event_bus.py]
        OSAL[os/manager.py]
        FilesCap[capabilities/files/manager.py]
    end

    %% Dependencies
    Assistant -->|depends on| IAgentBrain
    Assistant -->|depends on| IMemoryManager
    Assistant -->|depends on| IEventBus
    Assistant -->|depends on| IOSAdapter
    
    Planner -->|depends on| IAgentBrain
    Planner -->|depends on| IEventBus
    
    Dispatcher -->|depends on| IEventBus
    Dispatcher -->|depends on| ICapability

    %% Implementation injections
    Agent -.->|implements| IAgentBrain
    Memory -.->|implements| IMemoryManager
    EventBus -.->|implements| IEventBus
    OSAL -.->|implements| IOSAdapter
    FilesCap -.->|implements| ICapability
```
