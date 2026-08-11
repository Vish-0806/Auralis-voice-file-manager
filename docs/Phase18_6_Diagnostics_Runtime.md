# Phase 18.6 — Diagnostics Runtime

## Objective
The Diagnostics Runtime is a provider-independent, strongly typed diagnostic aggregation layer for the Auralis Voice File Manager Frontend V2. It is responsible for coordinating diagnostic checks, executing them with timeout enforcement and exception isolation, aggregating health and severity status, and exposing reports, statistics, and bounded execution history.

## Architecture
The diagnostics subsystem follows a clean separation of concerns:

```
DiagnosticsRuntime
        │ (coordinates via Dependency Injection)
        ▼
DiagnosticsProvider
        │ (implements business logic, history, and stats tracking)
        ├──────────────────────┐
        ▼                      ▼
DiagnosticsRegistry      DiagnosticsExecutor
        │ (tracks sources &     │ (executes checks, measures duration,
        │  checks registration) │  normalizes errors, and enforces timeouts)
        ▼                      ▼
Diagnostic Sources       Diagnostic Checks
```

- **DiagnosticsRuntime**: Thin dependency injection wrapper delegating actions to `DiagnosticsProvider`.
- **DiagnosticsProvider**: Core coordinator managing provider lifecycle, aggregating findings, maintaining bounded FIFO history, and tracking run-level metrics.
- **DiagnosticsRegistry**: Map-backed repository for sources and checks. Rejects duplicate registrations, preserves insertion order, and cascades unregistrations (removes checks when a source is removed).
- **DiagnosticsExecutor**: Performs the actual check runs, handles sync/async promises, measures execution duration, isolates error exceptions, and maps them to normalized result objects.

---

## Directory Structure
All runtime files are placed under the following structure:

```
frontend/src/observability/diagnostics/
├── models/
│   ├── diagnostic.ts      # DiagnosticSeverity, DiagnosticStatus, DiagnosticCategory, DiagnosticRecord
│   ├── source.ts          # DiagnosticSourceDescriptor
│   ├── check.ts           # DiagnosticCheck & callback interface
│   ├── result.ts          # DiagnosticResult & NormalizedErrorInfo
│   ├── report.ts          # DiagnosticReport
│   ├── statistics.ts      # DiagnosticsStatistics
│   └── index.ts           # Re-exports all models
│
├── interfaces/
│   ├── diagnostics-source.ts    # IDiagnosticsSource
│   ├── diagnostics-provider.ts  # IDiagnosticsProvider
│   ├── diagnostics-runtime.ts   # IDiagnosticsRuntime
│   └── index.ts                 # Re-exports all interfaces
│
├── registry/
│   └── DiagnosticsRegistry.ts   # Private Map-backed registry (insertion-ordered)
│
├── executor/
│   └── DiagnosticsExecutor.ts   # Error-isolating check executor with timeout handling
│
├── provider/
│   └── DiagnosticsProvider.ts   # Core lifecycle & report aggregation engine
│
├── runtime/
│   └── DiagnosticsRuntime.ts    # Thin DI coordinator
│
├── errors/
│   └── DiagnosticsErrors.ts     # Standardized typed runtime errors
│
├── factories/
│   └── diagnosticsFactories.ts  # Validation and deep freezing builders
│
└── index.ts                     # Entrypoint exporting public API
```

---

## Domain Models

### Diagnostic Severity
Exposes severity levels to rank findings:
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

### Diagnostic Status
Represents the operational health status of checked components:
- `HEALTHY`
- `DEGRADED`
- `UNHEALTHY`
- `UNKNOWN`
- `DISABLED`

### Diagnostic Category
Categorizes diagnostic checks for easier inspection:
- `RUNTIME`, `PERFORMANCE`, `AVAILABILITY`, `SECURITY`, `CONFIGURATION`, `DEPENDENCY`, `RESOURCE`, `INTEGRATION`, `CUSTOM`

### Diagnostic Record
An immutable record capturing diagnostic metadata:
- `id`, `sourceId`, `componentId`, `category`, `severity`, `status`, `title`, `message`, `timestamp`, `duration`, `metadata`, `relatedIdentifiers`

---

## Sources & Checks

### Diagnostic Sources
A diagnostic source represents a subsystem capable of running checks, described by an `IDiagnosticsSource` containing a `DiagnosticSourceDescriptor`:
- `id`
- `name`
- `description`
- `version` (optional)
- `enabled` (boolean)
- `priority`
- `metadata`

Conceptual examples include monitoring, logging, metrics, tracing, and telemetry.

### Diagnostic Checks
A diagnostic check exposes an executable callback (`execute`) returning a `DiagnosticStatusValue` (or `void` indicating success):
- `id`, `sourceId`, `name`, `description`, `category`, `severity`, `enabled`, `timeout` (ms), `priority`, `execute`

---

## Executor & Timeout Behavior

### Execution Mechanics
`DiagnosticsExecutor` runs synchronous and asynchronous callbacks. It runs checks using `Promise.resolve()` and races it against a timeout timer if a timeout is configured. 

### Timeout Handling
If a check's execution duration exceeds its specified `timeout` limit:
- The execution promise is rejected with a `DiagnosticTimeoutError`.
- The executor catches it, sets the status to `UNHEALTHY`, and logs the timeout message.
- A normalized error payload is added to the result containing stack information.
- The timeout timer is cleared properly to prevent memory leaks.

### Failure Isolation
If a check callback throws an exception or rejects:
- The executor isolates the error and formats it into a JSON-serializable `NormalizedErrorInfo` object (`name`, `message`, `stack`), preventing raw JS `Error` object leakages.
- The diagnostic run continues uninterrupted for all other registered checks.

---

## Health & Severity Aggregation

Deterministic rules are applied during report generation:

### Overall Status Aggregation
- **UNKNOWN**: When no enabled checks exist in the diagnostic run.
- **HEALTHY**: When all enabled results are `HEALTHY`.
- **DEGRADED**: When no result is `UNHEALTHY` but at least one enabled check result is `DEGRADED`.
- **UNHEALTHY**: When any enabled result is `UNHEALTHY`.

### Severity Aggregation
- Evaluated as: `CRITICAL > ERROR > WARNING > INFO`.
- The overall severity is determined by the highest severity value found among all enabled checks.
- Disabled checks are marked as `DISABLED` status and skipped; they do not impact overall status or severity evaluations.

---

## Provider Lifecycle
`DiagnosticsProvider` implements the following state transitions:

```
 UNINITIALIZED
       │
       ▼ (initialize())
  INITIALIZING
       │
       ▼
     READY <────────────┐
       │                │
       ▼ (run())        │
    RUNNING ────────────┘
       │
       ▼ (shutdown())
   STOPPING
       │
       ▼
    STOPPED
```

- **Idempotency**: Multiple calls to `initialize()` or `shutdown()` in stable states are safe no-ops.
- **State Enforcement**: Calling execution methods (`run`, `runSource`, `runCheck`) or modifying registries when `UNINITIALIZED` or `STOPPED` triggers a `DiagnosticsStateError`.

---

## Report Generation
When running diagnostics, the provider produces an immutable `DiagnosticReport`:
- `reportId`: Unique identifier.
- `generatedAt`: Epoch timestamp.
- `runtimeState`: State of the provider during execution.
- `overallStatus` / `overallSeverity`: Evaluated from aggregation.
- Source/check counters: `sourceCount`, `checkCount`, `passedCount`, `degradedCount`, `failedCount`, `skippedCount`.
- `results`: Array of individual `DiagnosticResult` objects.
- `summary`: A human-readable text string summarizing the findings.
- `statistics`: Historical statistics up to the generation time.

---

## History & Statistics

### Bounded History
- The provider stores diagnostic reports in an in-memory FIFO queue.
- The history capacity is configurable (defaults to `50` reports) to prevent unbounded memory growth.
- Newest reports are inserted at the head of the array (index `0`).
- History can be retrieved via `getHistory()` or cleared via `clearHistory()`. No files or databases are used for persistence.

### Statistics Tracking
Maintains run-level stats:
- `totalRuns`, `successfulRuns`, `degradedRuns`, `failedRuns`
- `skippedChecks`, `executedChecks`, `failedChecks`, `timedOutChecks`
- `totalDuration`, `averageDuration`
- `sourceCount`, `checkCount`

Returned statistics are immutable, deep-frozen snapshots.

---

## Operational Diagnostics Snapshot
`getDiagnostics()` returns the runtime's own metadata for system health checks:
- `runtimeState`
- `sourceCount` / `enabledSourceCount`
- `checkCount` / `enabledCheckCount`
- `historySize`
- `statistics`
- `generatedAt`

---

## Concurrency
To prevent state corruption:
- Multiple concurrent calls to `run()` resolve to the same active run promise.
- This ensures only one run coordinates diagnostic check execution at a time, protecting history queue sizes and statistics from double-counting.
- No global locks are introduced.

---

## Immutability
All returned models, records, results, reports, history, statistics, and snapshot objects are deeply frozen via `freezeDeepSafe`. Any attempt to mutate properties (e.g. `report.overallStatus = 'HEALTHY'`) throws a runtime exception in strict mode.

---

## Dependency Injection
`DiagnosticsRuntime` supports:
- `new DiagnosticsRuntime()` (instantiates standard in-memory provider)
- `new DiagnosticsRuntime(customProvider)` (injects custom provider)

The runtime does not implement business logic, ensuring standard pluggability.

---

## Testing
Comprehensive behavior tests are added under `frontend/tests/observability/diagnostics/`:
1. **`diagnostics_registry.test.ts`**: Verifies source/check mapping, cascading removal, ordering, and duplicate rejections.
2. **`diagnostics_executor.test.ts`**: Verifies synchronous, asynchronous, timeout, exception isolation, and duration tracking.
3. **`diagnostics_provider.test.ts`**: Verifies lifecycle transitions, run capabilities, bounded history, and concurrency safety.
4. **`diagnostics_aggregation.test.ts`**: Validates status and severity ranking rules.
5. **`diagnostics_immutability.test.ts`**: Verifies deep freezing on all factory outputs.
6. **`diagnostics_performance.test.ts`**: Verifies performance and lookup characteristics.

---

## Actual Performance Measurements
Below are the actual benchmark times measured during the Vitest run:
- **Source Lookup Time**: `0.000556 ms` / lookup (~0.56 microseconds)
- **Check Lookup Time**: `0.000508 ms` / lookup (~0.51 microseconds)
- **Full Run & Report Aggregation Time** (50 checks across 10 sources): `1.4717 ms` / run
- **Snapshot Generation Time**: `0.073703 ms` / snapshot (~73.7 microseconds)

---

## Known Limitations
- **In-Memory Only**: Reports and history do not survive app restarts/refreshes.
- **Single-Threaded CPU Timeout**: Synchronous loops in check callbacks will block the main thread and cannot be forcibly aborted mid-execution, though they will be categorized as timeouts after execution yields.

---

## Strict Phase Boundaries
- **No Alerting or Notifications**: Phase 18.7 (email, Slack, push notification deliveries) is NOT implemented.
- **No Dashboards or Visualizations**: Phase 18.8 (UI diagnostic pages) is NOT implemented.
- **No Direct Subsystem Integrations**: Phase 18.9 (integrating Logging, Metrics, Tracing, Telemetry provider data) is NOT implemented. No dependencies on external platforms like OpenTelemetry are present.
- **No Persistent Storage**: Filesystem or database syncing is out of scope.
