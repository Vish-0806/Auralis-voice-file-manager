# System Capabilities Subsystem

## Capability Registration & Discovery
Capabilities in Auralis are modular plugins that extend the assistant's functional capacity. Every capability class implements the `ICapability` interface and registers itself with the central `CapabilityRegistry`.

During system bootstrap:
1. **Scans packages:** The `CapabilityManager` scans the `backend/capabilities/` sub-directories.
2. **Registers tools:** It instantiates active capabilities and registers them in the `CapabilityRegistry`.
3. **Dispatcher Discovery:** The `ActionDispatcher` queries the `CapabilityRegistry` to resolve target actions dynamically at runtime.
4. **Third-Party Plugins:** Future plugins can register new capabilities dynamically by calling `CapabilityRegistry.register()` during initialization.

---

## Architectural Relationships

```mermaid
graph TD
    %% Core Orchestrator
    subgraph Core [core/]
        Assistant[AuralisAssistant]
        Dispatcher[ActionDispatcher]
    end

    %% Registry & Manager
    subgraph CapabilitySub [capabilities/]
        Manager[CapabilityManager]
        Registry[CapabilityRegistry]
    end

    %% Capabilities
    subgraph CapabilityPackages [Capability Packages]
        Files[Files Capability]
        Desktop[Desktop Capability]
        Dev[Developer Capability]
        Doc[Documents Capability]
        Auto[Automation Capability]
        Sys[System Capability]
    end

    %% Interfaces
    OSAL[OS Abstraction Layer]
    AI[AI Brain]
    Events[Event Bus]

    %% Wiring
    Assistant -->|1. Process Request| AI
    AI -->|2. Query active tool definitions| Registry
    Assistant -->|3. Dispatch plan steps| Dispatcher
    Dispatcher -->|4. Query matching action| Registry
    Registry -->|5. Resolve instance| Files & Desktop & Dev & Doc & Auto & Sys
    
    Files & Desktop & Dev & Doc & Auto & Sys -->|6. Execute OS calls| OSAL
    Files & Desktop & Dev & Doc & Auto & Sys -->|7. Log outcomes| Events
```
