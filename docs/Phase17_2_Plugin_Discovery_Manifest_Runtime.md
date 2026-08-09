# Phase 17.2 — Plugin Discovery & Manifest Runtime

## Objective

Establish a production-quality, provider-independent Plugin Discovery & Manifest Runtime. This phase introduces discovery source abstractions, manifest acquisition, manifest parsing, schema and version syntax validation, duplicate plugin detection, and validated manifest registration.

## Architecture

The discovery system is designed to be pure TypeScript and provider-independent, ensuring it does not depend on filesystem, network, React, JSX, Zustand, or browser-specific globals. It cleanly separates:
- **Domain Models**: Models for manifest, author, dependencies, capabilities, statistics, and health.
- **Interfaces**: Contracts for discovery sources and managers.
- **Validation Engines**: Syntax validation for SemVer and semantic range formats.
- **Discovery Manager**: Coordinating discovery execution across sources, filtering duplicates, parsing schemas, and managing active valid manifests.
- **Provider/Runtime Integration**: Delegating discovery operations through the provider/runtime coordinators.

## Directory Structure

All files reside in the pure TypeScript plugins directory:
- `src/plugins/models/manifest.ts`: Contains domain models and types.
- `src/plugins/interfaces/plugin-discovery.ts`: Contains discovery manager/source interfaces.
- `src/plugins/runtime/SemVerValidator.ts`: Handles SemVer 2.0.0 and range syntax checks.
- `src/plugins/runtime/PluginManifestValidator.ts`: Handles manifest parsing and schema validation rules.
- `src/plugins/runtime/InMemoryDiscoverySource.ts`: Implements a safe memory-only candidate source.
- `src/plugins/runtime/PluginDiscoveryManager.ts`: Coordinates register, discover, lookup, and diagnostics.

## Manifest Structure

The plugin manifest model (`PluginManifest`) defines the structural schema for plugins:
- `id` (string): Unique identifier (alphanumeric, dots, hyphens, underscores, no spaces).
- `name` (string): Human-readable plugin name.
- `version` (string): SemVer version.
- `description` (optional string): Short summary of the plugin.
- `author` (string or PluginAuthor): Author name, email, and URL.
- `schemaVersion` (string): Schema version identifier.
- `entryPoint` (string): File entry path.
- `dependencies` (array): Declared prerequisite plugins with version ranges.
- `capabilities` (array): Declared capabilities.
- `metadata` (optional Record): Additional custom fields.

## Validation Rules

1. **Required Fields**: Reject if `id`, `name`, `version`, `author`, `schemaVersion`, or `entryPoint` are missing/empty.
2. **Plugin ID**: Must not contain spaces. Must match `/^[a-zA-Z0-9._-]+$/`.
3. **SemVer Syntax**: Plugin version must match the strict `MAJOR.MINOR.PATCH` pattern, with optional prerelease identifiers and build metadata.
4. **Dependency Declarations**: Range syntax checked against wildcards and comparison operators (e.g. `^1.0.0`, `~1.2.3`, `*`, `1.x`).
5. **Capability Declarations**: Must have non-empty types and valid object property dictionaries.
6. **Duplicate Declarations**: Checks that dependencies or capabilities are not defined multiple times within the same manifest.

## SemVer syntax validation

- Supports `MAJOR.MINOR.PATCH`.
- Supports prerelease identifiers (e.g. `-alpha.1`).
- Supports build metadata (e.g. `+build.123`).
- Rejects malformed version strings.
- Pads ranges to three parts (e.g., `1.x` parses as `1.0.0`) to validate syntax against SemVer format constraints.

## Discovery Source Abstraction

The core runtime uses the `IPluginDiscoverySource` interface, abstracting where manifests originate.
- Core runtime does not know whether manifests come from memory, filesystem, remote API, or database.
- Implements an `InMemoryDiscoverySource` for deterministic test verification.

## Duplicate Handling

- Duplicate plugin IDs are never silently overwritten.
- If a plugin ID is already registered or discovered in the current run, the second registration is rejected, throwing `PluginDuplicateError`.
- Duplicate attempts increment telemetry statistics.

## Provider/Runtime Delegation

The runtime coordinators remain clean, thin coordinators:
`PluginRuntime` delegates to `PluginProvider`, which delegates to the `PluginDiscoveryManager`.
- This ensures dependency injection patterns are fully preserved.

## Diagnostics

- **Statistics**: Tracks `discoveryAttempts`, `discoveredPlugins`, `validManifests`, `invalidManifests`, `duplicateAttempts`, `discoveryFailures`, `validationFailures`, and `registeredSources`.
- **Health**: Health reports warning conditions and active failures.

## Explicit Phase boundaries

### Strictly Deferred to Phase 17.3
- Dependency graph resolution, topological sorting (Kahn's algorithm), and conflict resolution.
- Parsing and resolution of version range overlap graphs.

### Strictly Deferred to Future Phases
- Dynamic imports (`import()`) or remote code execution.
- Sandboxing or capability execution.
- Activation and deactivation workflows.
- User interface or settings screens.
