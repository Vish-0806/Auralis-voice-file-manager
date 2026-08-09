# Phase 17.1 Plugin Runtime Foundation

## Objective

Establish the foundation for a provider-independent plugin and extension runtime for Frontend V2. This phase introduces immutable domain models, a thin provider abstraction, and a runtime coordinator without implementing discovery, loading, sandboxing, lifecycle workflows beyond basic initialization and shutdown, or capability execution.

## Architecture

The runtime core is intentionally pure TypeScript and does not depend on React, JSX, DOM APIs, Zustand, Axios, or browser-specific globals. The design separates:

- domain models in the plugins/models layer
- provider contracts in plugins/interfaces
- implementation in plugins/provider
- orchestration in plugins/runtime
- factories for simple construction

## Directory Structure

- plugins/models: plugin, plugin state, and runtime state models
- plugins/interfaces: provider and runtime contracts
- plugins/provider: PluginProvider implementation
- plugins/runtime: PluginRuntime coordinator
- plugins/errors: plugin-specific runtime errors
- plugins/factories: simple factory helpers

## Runtime/Provider Separation

The coordinator class delegates all public operations to an injected provider implementing the provider contract. This keeps business logic out of the coordinator and enables tests and future integrations to inject custom providers without changing the runtime surface.

## Plugin State Model

Plugins are modeled with an explicit state machine:

- UNREGISTERED
- REGISTERED
- INITIALIZING
- READY
- DISABLED
- ERROR
- DISPOSED

The foundation uses these values to represent lifecycle and registration state without performing actual loading.

## Runtime Lifecycle

The runtime lifecycle is limited to initialization and shutdown:

- initialize transitions UNINITIALIZED -> INITIALIZING -> READY
- shutdown transitions READY -> STOPPING -> STOPPED
- invalid transitions are handled safely and do not mutate state unexpectedly

## Registration Behavior

Plugin registration validates metadata, rejects duplicate plugin IDs, creates a registered plugin snapshot, and returns a deterministic result. Unregistration removes the plugin and ensures missing plugins raise a clear state error.

## Error Hierarchy

The runtime defines a hierarchy of plugin errors:

- PluginRuntimeError
- PluginInitializationError
- PluginRegistrationError
- PluginValidationError
- PluginStateError

Each error preserves the prototype chain and stack trace.

## Dependency Injection

The runtime constructor accepts an optional provider instance. When none is supplied, a default PluginProvider is used. This keeps the runtime testable and avoids module-level singleton state.

## Immutability Strategy

All public domain objects are frozen with Object.freeze. Internal maps are not exposed, and returned snapshots are copied so callers cannot mutate provider state through returned references.

## Testing Strategy

Vitest tests exercise the runtime contract without browser APIs, network calls, filesystem access, React rendering, or Zustand.

## Explicit Phase 17.1 Boundaries

Phase 17.1 intentionally does not implement:

- plugin discovery
- manifest loading
- dependency resolution
- lifecycle management beyond basic initialization/shutdown
- sandboxing
- capability registration
- marketplace support
- plugin settings UI
- dynamic remote code loading
- plugin installation
- plugin activation/deactivation workflows

## Deferred to 17.2–17.10

These concerns remain for later phases:

- discovery and manifest parsing
- dependency handling
- capability registration and execution
- remote loading and installation
- activation and deactivation flows
- UI and configuration surfaces
