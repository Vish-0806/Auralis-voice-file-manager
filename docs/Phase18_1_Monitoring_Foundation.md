# Auralis V2 Observability & Operations Runtime
## Phase 18.1 — Monitoring Foundation

---

## 1. Phase Objective

Establish a clean, provider-independent monitoring foundation that will later support logging, metrics, tracing, telemetry, diagnostics, alerting, and the monitoring dashboard. This phase creates the core runtime, provider, and registry abstractions without any external dependencies.

---

## 2. Architecture

```
MonitoringRuntime (thin coordinator, DI support)
        |
        v
MonitoringProvider (business logic, lifecycle, execution)
        |
        v
MonitoringRegistry (component & check storage, O(1) lookup)
```

**MonitoringRuntime** is an intentionally thin delegation layer. It accepts an optional `IMonitoringProvider` via constructor injection and forwards every public operation to the provider. It contains zero business logic.

**MonitoringProvider** owns monitoring state: the lifecycle state machine, the registry, statistics counters, check execution, health aggregation, and diagnostics snapshots.

**MonitoringRegistry** owns the private `Map<string, MonitoringComponent>` and `Map<string, MonitoringCheck>` collections. It enforces uniqueness constraints, validates referential integrity (checks must reference existing components), and returns immutable snapshots.

---

## 3. Directory Structure

```
frontend/src/observability/
├── models/
│   ├── monitoring.ts        # Domain models, freezeDeepSafe utility
│   ├── health.ts            # MonitorStatus, MonitoringHealth
│   ├── runtime.ts           # MonitoringRuntimeState
│   └── index.ts             # Barrel exports
├── interfaces/
│   ├── monitoring-provider.ts  # IMonitoringProvider
│   ├── monitoring-runtime.ts   # IMonitoringRuntime
│   └── index.ts
├── provider/
│   └── MonitoringProvider.ts
├── runtime/
│   └── MonitoringRuntime.ts
├── registry/
│   └── MonitoringRegistry.ts
├── errors/
│   └── MonitoringErrors.ts
├── factories/
│   └── monitoringFactories.ts
└── index.ts                  # Root barrel exports

frontend/tests/observability/
└── monitoring_foundation.test.ts   # 31 tests
```

---

## 4. Provider/Runtime Separation

| Concern | MonitoringRuntime | MonitoringProvider |
|---|---|---|
| Lifecycle state | Delegates | Owns |
| Registry | Delegates | Owns |
| Check execution | Delegates | Owns |
| Statistics | Delegates | Owns |
| Health aggregation | Delegates | Owns |
| DI support | Constructor injection | N/A |
| Business logic | None | All |

---

## 5. Domain Models

| Model | Purpose |
|---|---|
| `MonitoringRuntimeState` | Lifecycle enum: UNINITIALIZED → INITIALIZING → READY → STOPPING → STOPPED, plus ERROR |
| `MonitorStatus` | Health enum: UNKNOWN, HEALTHY, DEGRADED, UNHEALTHY, DISABLED |
| `MonitoringComponentType` | Category enum: RUNTIME, SERVICE, SUBSYSTEM, PROVIDER, EXTERNAL |
| `MonitoringComponent` | Registered monitoring target with id, name, type, status, enabled, timestamps, metadata |
| `MonitoringCheck` | Executable health check with id, componentId, name, executionOrder, timeoutMs, execute callback |
| `MonitoringCheckCallback` | Typed callback: `() => void | Promise<void> | MonitorStatusValue | Promise<MonitorStatusValue>` |
| `MonitoringResult` | Execution outcome with checkId, componentId, status, timing, optional error |
| `MonitoringStatistics` | Aggregated counters: total, successful, degraded, failed, skipped, timing |
| `MonitoringHealth` | Aggregated health: status, component counts, warnings |
| `MonitoringDiagnostics` | Snapshot: runtimeState, counts, statistics, health, generatedAt |

---

## 6. Registry Design

- Components and checks stored in private `Map` instances
- Component IDs and check IDs must be unique (duplicate registration throws `MonitoringRegistrationError`)
- Check registration validates that the target `componentId` exists
- Unregistering a component cascades to delete all associated checks
- `listComponents()` returns deterministic alphabetical order by ID
- `listChecks()` returns deterministic order by `executionOrder` ascending, then ID alphabetically
- All returned objects are deep-frozen defensive copies

---

## 7. Lifecycle State Machine

```
UNINITIALIZED → INITIALIZING → READY → STOPPING → STOPPED
                      ↓ (on error)
                    ERROR
```

- `initialize()` is idempotent (no-op if already READY)
- `shutdown()` is idempotent (no-op if already STOPPED)
- Cannot initialize from STOPPED state
- Cannot shutdown from UNINITIALIZED state
- All provider operations require READY state

---

## 8. Check Execution

- Supports synchronous callbacks (`() => void`)
- Supports asynchronous callbacks (`() => Promise<void>`)
- Supports status-returning callbacks (`() => MonitorStatusValue`)
- Disabled checks produce a DISABLED/skipped result without invoking the callback
- Thrown exceptions are caught and produce UNHEALTHY results (crash isolation)
- Thrown exceptions with a `.status` property use that status (e.g., DEGRADED)
- Each execution measures `startedAt`, `completedAt`, and `durationMs`
- Component status is updated to the worst status across its checks after execution

---

## 9. Health Aggregation

| Condition | Aggregate Status |
|---|---|
| No registered components | UNKNOWN |
| All enabled components disabled | UNKNOWN |
| All enabled components HEALTHY | HEALTHY |
| ≥1 enabled DEGRADED, 0 UNHEALTHY | DEGRADED |
| ≥1 enabled UNHEALTHY | UNHEALTHY |

Disabled components do not influence the aggregate status.

---

## 10. Statistics

Tracked counters:
- `totalChecks` — total executions (including skipped)
- `successfulChecks` — HEALTHY results
- `degradedChecks` — DEGRADED results
- `failedChecks` — UNHEALTHY results
- `skippedChecks` — DISABLED results
- `totalExecutionTimeMs` — cumulative execution duration
- `averageExecutionTimeMs` — average over non-skipped checks
- `lastCheckAt` — timestamp of most recent execution

---

## 11. Diagnostics Foundation

`getDiagnostics()` returns an immutable snapshot containing:
- `runtimeState`
- `componentCount`
- `checkCount`
- `statistics`
- `health`
- `generatedAt`

---

## 12. Error Hierarchy

| Error Class | Purpose |
|---|---|
| `MonitoringRuntimeError` | Base error for all monitoring errors |
| `MonitoringInitializationError` | Initialization failures |
| `MonitoringRegistrationError` | Duplicate registration attempts |
| `MonitoringValidationError` | Invalid input data |
| `MonitoringStateError` | Invalid lifecycle transitions |
| `MonitoringComponentNotFoundError` | Missing component lookups |
| `MonitoringCheckNotFoundError` | Missing check lookups |
| `MonitoringCheckExecutionError` | Check execution failures |

All errors extend `Error` correctly with `Object.setPrototypeOf` and `Error.captureStackTrace`.

---

## 13. Immutability

- All public return values are deep-frozen using `freezeDeepSafe()`
- `freezeDeepSafe` recursively copies and freezes plain objects, arrays, Maps, and Sets
- Already-frozen objects are returned as-is (no re-copy)
- Internal mutable Maps are never exposed
- Callers cannot mutate provider state through returned objects

---

## 14. Dependency Injection

```typescript
// Default provider
const runtime = new MonitoringRuntime();

// Custom/mock provider
const mockProvider: IMonitoringProvider = { ... };
const runtime = new MonitoringRuntime(mockProvider);
```

---

## 15. Performance Targets

- Component registration: < 1 ms
- Component lookup: < 1 ms
- Check registration: < 1 ms
- Check lookup: < 1 ms
- Health evaluation: < 5 ms

These are sanity-checked in the test suite (test #31).

---

## 16. Testing Strategy

31 tests in `monitoring_foundation.test.ts` covering:
1. Default and injected provider construction
2. Lifecycle transitions (init, shutdown, idempotency, invalid states)
3. Component CRUD (register, lookup, list, unregister, cascade delete)
4. Check CRUD (register, lookup, list, unregister)
5. Sync and async check execution
6. Crash isolation and exception handling
7. Health aggregation rules
8. Statistics aggregation
9. Immutability and defensive snapshots
10. Missing component/check errors
11. Provider and runtime delegation
12. Registry clearing
13. Diagnostics snapshots
14. Performance sanity checks

---

## 17. Explicit Boundaries — What Phase 18.1 Does NOT Implement

- ❌ Logging runtime
- ❌ Metrics collection
- ❌ Distributed tracing
- ❌ OpenTelemetry integration
- ❌ Telemetry export
- ❌ Alerting / notifications
- ❌ Monitoring dashboard UI
- ❌ External monitoring providers (Prometheus, Sentry, Datadog, etc.)
- ❌ Production certification
- ❌ Scheduled check execution
- ❌ Retry logic
- ❌ Integration with Phase 16 or Phase 17 runtimes

These will be introduced in subsequent Phase 18.x subphases.
